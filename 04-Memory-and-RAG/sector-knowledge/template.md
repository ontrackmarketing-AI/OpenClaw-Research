# Sector Knowledge Base Template

Use this template when creating a new sector knowledge base for OpenClaw's multi-sector RAG system. Copy this file, rename it to match the sector, and fill in every section. Incomplete sections should be marked `[TODO]` with a note on where to source the data.

**File naming:** `sector-knowledge/{sector-slug}.md` (e.g., `healthcare-dental.md`, `legal.md`, `real-estate.md`)

---

## Instructions for Creating a New Sector Knowledge Base

### Step 1: Fill in this template

Complete every section below with sector-specific data. Sources for each section are listed at the bottom. Aim for enough detail that an AI agent can generate personalized outreach, recommend marketing strategies, and answer client questions without additional research.

### Step 2: Create supporting documents

Beyond this master file, create detailed documents in the sector's `documents/` directory:

```
~/.openclaw/memory/knowledge/{sector-slug}/
  documents/
    pain-points.md              # Expanded pain points with examples
    channel-effectiveness.md    # Detailed channel analysis with benchmarks
    pricing-benchmarks.md       # Detailed pricing data, updated quarterly
    case-studies/
      case-study-001.md         # Individual case studies
      case-study-002.md
    compliance.md               # Full regulatory details
    outreach-templates.md       # All outreach templates for this sector
    seasonal-playbook.md        # Month-by-month marketing recommendations
    competitor-analysis.md      # Detailed competitor breakdown
```

### Step 3: Ingest into the knowledge base

```bash
# Create the sector database
python ingest_sector.py \
  --sector {sector-slug} \
  --source ~/.openclaw/memory/knowledge/{sector-slug}/documents/ \
  --db ~/.openclaw/memory/knowledge/{sector-slug}/index.db \
  --model nomic-embed-text

# Verify ingestion
python verify_ingestion.py \
  --db ~/.openclaw/memory/knowledge/{sector-slug}/index.db
```

### Step 4: Register with OpenClaw's routing

Add the new sector to the `SectorRouter` in `multi-sector-rag.md`:

```python
# In SectorRouter.SECTOR_KEYWORDS, add:
Sector.{SECTOR_ENUM}: [
    "keyword1", "keyword2", "keyword3",
    # ... keywords that identify this sector in queries
],
```

Update the `Sector` enum:

```python
class Sector(Enum):
    SMB_LOCAL = "smb-local-services"
    SOLAR_HOME = "solar-home-improvement"
    HEALTHCARE = "healthcare-dental"
    LEGAL = "legal"
    REAL_ESTATE = "real-estate"
    {NEW_SECTOR} = "{sector-slug}"       # <-- add this line
    GENERAL = "general"
```

### Step 5: Test the routing

```python
router = SectorRouter()

# Test that queries route to the new sector
test_queries = [
    "What's the best marketing channel for {sector business type}?",
    "{sector-specific keyword} lead generation",
    "How much does a {sector business type} spend on marketing?",
]
for q in test_queries:
    sectors = router.route(q)
    assert Sector.{NEW_SECTOR} in sectors, f"Routing failed for: {q}"
    print(f"  '{q}' -> {[s.value for s in sectors]}")
```

---

# {SECTOR NAME} -- Knowledge Base

> **Status:** [Draft / In Progress / Complete]
> **Last Updated:** [YYYY-MM-DD]
> **Author:** [Name]
> **Review Cycle:** [Quarterly / Semi-annually]

---

## 1. Sector Overview

[2-3 paragraphs describing the sector: what these businesses do, their typical size, how they make money, and what makes marketing in this sector unique.]

**Key characteristics:**
- [Characteristic 1]
- [Characteristic 2]
- [Characteristic 3]

---

## 2. Target Business Types

| Sub-Industry | Typical Size | Avg Revenue | Avg Deal Size | Sales Cycle | Marketing Maturity |
|-------------|-------------|-------------|--------------|-------------|-------------------|
| [Type 1] | [X-Y employees] | [$X-Y] | [$X-Y] | [X-Y days] | [Low/Medium/High] |
| [Type 2] | | | | | |
| [Type 3] | | | | | |
| [Type 4] | | | | | |
| [Type 5] | | | | | |

---

## 3. Industry Pain Points

For each pain point, document:
- The exact words business owners use (for outreach personalization)
- The underlying root cause
- The corresponding Rise Local signal (if applicable)
- The recommended solution

### Pain Point: "[Exact quote from business owner]"
- **Translation:** [What they actually mean]
- **Root cause:** [Why this is happening]
- **Rise Local signal:** [Signal # and name, or N/A]
- **Solution:** [Recommended marketing approach]
- **Objection handling:** [Common pushback and response]

### Pain Point: "[Exact quote]"
- **Translation:**
- **Root cause:**
- **Rise Local signal:**
- **Solution:**
- **Objection handling:**

### Pain Point: "[Exact quote]"
- **Translation:**
- **Root cause:**
- **Rise Local signal:**
- **Solution:**
- **Objection handling:**

[Add 5-10 pain points per sector. More is better.]

---

## 4. Average Marketing Budget

| Sub-Industry | Monthly Budget Range | Sweet Spot | % of Revenue | Notes |
|-------------|---------------------|-----------|-------------|-------|
| [Type 1] | $[X] - $[Y] | $[Z] | [X-Y]% | |
| [Type 2] | | | | |
| [Type 3] | | | | |

**Budget allocation recommendation:**
- [X]% [Channel 1]
- [X]% [Channel 2]
- [X]% [Channel 3]
- [X]% Tools and tracking
- [X]% Creative and content

---

## 5. Effective Marketing Channels

### Tier 1: Must-Have (Highest ROI)

| Channel | Typical CPL | Conversion Rate | Setup Effort | Ongoing Effort | Notes |
|---------|-----------|----------------|-------------|---------------|-------|
| [Channel 1] | $[X-Y] | [X-Y]% | [Low/Med/High] | [Low/Med/High] | |
| [Channel 2] | | | | | |

### Tier 2: High Value

| Channel | Typical CPL | Conversion Rate | Setup Effort | Ongoing Effort | Notes |
|---------|-----------|----------------|-------------|---------------|-------|
| [Channel 3] | | | | | |
| [Channel 4] | | | | | |

### Tier 3: Supplemental

| Channel | Typical CPL | Conversion Rate | Notes |
|---------|-----------|----------------|-------|
| [Channel 5] | | | |

### Channel Recommendations by Sub-Industry

| Sub-Industry | Primary Channel | Secondary Channel | Avoid |
|-------------|----------------|-------------------|-------|
| [Type 1] | | | |
| [Type 2] | | | |

---

## 6. Key Performance Metrics

### Benchmarks

| Metric | Good | Great | Industry Avg | How to Measure |
|--------|------|-------|-------------|---------------|
| Cost Per Lead | $[X] | $[X] | $[X] | [Tool/method] |
| Close Rate | [X]% | [X]% | [X]% | CRM data |
| Avg Deal Size | $[X] | $[X] | $[X] | CRM data |
| Customer LTV | $[X] | $[X] | $[X] | Revenue analysis |
| CPA | $[X] | $[X] | $[X] | Spend / conversions |
| ROAS | [X]:1 | [X]:1 | [X]:1 | Revenue / ad spend |
| Speed to Lead | [X] min | [X] min | [X] min | Call tracking |

### KPIs to Report Monthly

1. [KPI 1]
2. [KPI 2]
3. [KPI 3]
4. [KPI 4]
5. [KPI 5]

---

## 7. Seasonal Patterns

| Month | Demand Level | Key Events/Drivers | Marketing Action |
|-------|-------------|-------------------|-----------------|
| Jan | [Low/Med/High] | | |
| Feb | | | |
| Mar | | | |
| Apr | | | |
| May | | | |
| Jun | | | |
| Jul | | | |
| Aug | | | |
| Sep | | | |
| Oct | | | |
| Nov | | | |
| Dec | | | |

**Budget adjustment strategy:** [How to shift spend based on seasonal demand]

---

## 8. Common Tech Stack

| Tool | Category | Typical Users | Price Range | Integration Notes |
|------|----------|--------------|-------------|-------------------|
| [Tool 1] | [CRM/FSM/Accounting/etc.] | [Who uses it] | $[X-Y]/mo | [API available? GHL integration?] |
| [Tool 2] | | | | |
| [Tool 3] | | | | |
| [Tool 4] | | | | |
| [Tool 5] | | | | |

**Integration opportunities:**
- [How the tech stack affects marketing approach]
- [Upsell opportunities based on tech gaps]

---

## 9. Regulatory / Compliance Requirements

### Federal

| Requirement | Details | Marketing Impact |
|------------|---------|-----------------|
| [Regulation 1] | | |
| [Regulation 2] | | |

### State-Specific (Primary Markets)

| State | Requirement | Details | Marketing Impact |
|-------|------------|---------|-----------------|
| [State 1] | | | |
| [State 2] | | | |

### Advertising Rules

- [Rule 1: What can/cannot be said in ads]
- [Rule 2]
- [Rule 3]

---

## 10. Competitor Landscape

### Major Competitors

| Competitor | Type | Strengths | Weaknesses | How to Compete Against |
|-----------|------|-----------|------------|----------------------|
| [Competitor 1] | [National/Regional/Local] | | | |
| [Competitor 2] | | | | |
| [Competitor 3] | | | | |

### Competitive Positioning

[How businesses in this sector should differentiate themselves from competitors. What unique value propositions work best.]

---

## 11. Integration with Rise Local Pipeline

### Signal Mapping

| Signal # | Signal Name | Relevance to This Sector | Auto-Response |
|----------|------------|------------------------|--------------|
| 1 | GBP Ranking | [High/Medium/Low/N/A] | [Pitch summary] |
| 2 | Review Count | | |
| 3 | Call Volume | | |
| 4 | Negative Reviews | | |
| 5 | Mobile Score | | |
| 6 | Page Speed | | |
| 7 | Organic Visibility | | |
| 8 | Social Activity | | |
| 9 | Ads Quality | | |
| 10 | High CPC | | |
| 11 | Third-Party Spend | | |
| 12 | No Call Tracking | | |
| 13 | Competitor Gap | | |
| 14 | Seasonal Readiness | | |
| 15 | Tech Stack Maturity | | |

### Sector-Specific Signals

[Are there any pain signals unique to this sector that Rise Local should add?]

---

## 12. Template Outreach Messages

### Cold Email: [Pain Point 1]

```
Subject: [Subject line]

Hi [Owner Name],

[Personalized opening referencing their specific pain point]

[Social proof / case study reference]

[Clear call to action]

[Signature]
```

### Cold Email: [Pain Point 2]

```
Subject: [Subject line]

[Body]
```

### LinkedIn DM: [General Outreach]

```
[Message]
```

### Cold Call Script Opening

```
"Hi [Name], this is [Your Name] with [Agency]. I'm calling because
[specific pain point observation]. Do you have 30 seconds for a
quick question about [topic]?"
```

[Create at least 3-5 outreach templates per sector, each targeting a different pain point.]

---

## 13. Case Study Framework

Use this structure for every case study in this sector:

```markdown
# Case Study: [Business Name] - [Sub-Industry]

## The Situation
- **Business:** [Name], [sub-industry] in [City, State]
- **Size:** [employees], [years in business]
- **Problem:** [1-2 sentences]
- **Before metrics:**
  - [Metric 1]: [value]
  - [Metric 2]: [value]
  - [Metric 3]: [value]

## What We Did
- **Services:** [list]
- **Timeline:** [X months]
- **Key actions:**
  1. [Action]
  2. [Action]
  3. [Action]

## The Results
- **After metrics (at [X] months):**
  - [Metric 1]: [value] ([% change])
  - [Metric 2]: [value] ([% change])
  - [Metric 3]: [value] ([% change])
- **ROI:** [X]:1
- **Client quote:** "[Quote]"
```

**Case studies needed for this sector:**
- [ ] [Sub-industry 1] success story
- [ ] [Sub-industry 2] success story
- [ ] [Sub-industry 3] success story
- [ ] Before/after with specific revenue numbers
- [ ] Competitive win story (won client from a competitor)

---

## 14. Knowledge Sources

Where to get and update the data for this sector:

| Data Needed | Source | Access Method | Cost | Update Frequency |
|-------------|--------|-------------|------|-----------------|
| Industry benchmarks | [Source] | [How to access] | [Free/$X] | Quarterly |
| CPL/CPA data | Internal campaign data | GHL/Google Ads reports | Free | Monthly |
| Compliance updates | [Regulatory body] | [Website/newsletter] | Free | Semi-annually |
| Competitor data | [Tools/manual research] | [Method] | [Cost] | Quarterly |
| Pain point language | Sales call recordings | [CRM/Gong/manual] | Free | Monthly |
| Seasonal patterns | Historical campaign data | [Analytics tool] | Free | Annually |
| Tech stack info | Client onboarding surveys | [Survey tool] | Free | Semi-annually |

---

## 15. Update Schedule

| Content Section | Update Frequency | Responsible | Last Updated | Next Update |
|----------------|-----------------|-------------|-------------|-------------|
| Pain Points | Quarterly | [Name] | [Date] | [Date] |
| Marketing Budgets | Quarterly | [Name] | [Date] | [Date] |
| Channel Effectiveness | Quarterly | [Name] | [Date] | [Date] |
| Performance Metrics | Monthly | [Name] | [Date] | [Date] |
| Seasonal Patterns | Annually | [Name] | [Date] | [Date] |
| Compliance | Semi-annually | [Name] | [Date] | [Date] |
| Competitor Landscape | Quarterly | [Name] | [Date] | [Date] |
| Outreach Templates | Monthly | [Name] | [Date] | [Date] |
| Case Studies | As completed | [Name] | [Date] | [Date] |
| Tech Stack | Semi-annually | [Name] | [Date] | [Date] |

**Update process:**
1. Check each section against the schedule above.
2. Gather updated data from the sources listed in Section 14.
3. Update the relevant markdown files in the `documents/` directory.
4. Run incremental ingestion: `python ingest_sector.py --sector {sector-slug} --incremental`
5. Run verification: `python verify_ingestion.py --db {sector-slug}/index.db`
6. Test 3-5 representative queries to confirm results reflect the updates.
7. Update the "Last Updated" column in the schedule above.
8. Log the update in the daily session log.

---

## Checklist Before Marking Sector Complete

- [ ] All 15 sections filled in (no remaining `[TODO]` markers)
- [ ] At least 5 pain points documented with owner-language quotes
- [ ] At least 3 outreach templates written and tested
- [ ] At least 1 case study with real numbers (anonymized if needed)
- [ ] Channel effectiveness data based on real campaigns (not just industry reports)
- [ ] Compliance section reviewed by someone with industry knowledge
- [ ] All supporting documents created in `documents/` directory
- [ ] Ingestion completed with zero errors
- [ ] Verification passed (all quality checks green)
- [ ] Routing tested (queries correctly route to this sector)
- [ ] 10 test queries produce relevant, accurate results
- [ ] Knowledge base registered in OpenClaw sector configuration
- [ ] Update schedule entered with responsible parties and dates

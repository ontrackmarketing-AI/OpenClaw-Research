# Multi-Sector RAG Architecture

## Concept

OnTrack Marketing serves clients across multiple industry verticals. Each industry has its own terminology, pain points, competitive dynamics, regulatory requirements, and marketing best practices. A single monolithic knowledge base would pollute results -- when a solar installer asks about lead costs, you do not want results about dental marketing mixed in.

Multi-sector RAG solves this by maintaining separate, curated knowledge bases per industry vertical, with an intelligent routing layer that directs queries to the appropriate sector(s).

---

## Why Separate Knowledge Bases

| Problem with Monolithic KB | How Sector Separation Fixes It |
|---------------------------|-------------------------------|
| "Cost per lead" means different things in different industries ($30 for plumber, $150 for solar) | Each sector has its own benchmarks and context |
| Compliance requirements differ (HIPAA for dental, ITC credits for solar, TDLR for Texas contractors) | Sector-specific regulatory knowledge stays isolated |
| Marketing channel effectiveness varies (Google Maps for plumbers, canvassing for solar) | Channel recommendations come from the right industry context |
| Search results get diluted with irrelevant cross-industry noise | Queries scoped to a sector return highly relevant results |
| One sector's jargon confuses embeddings for another | Embedding spaces are cleaner within a single domain |

---

## Architecture Options

### Option A: One SQLite Database Per Sector (Recommended for OpenClaw)

```
~/.openclaw/memory/knowledge/
  smb-local-services/
    index.db                  # SQLite with FTS5 + sqlite-vec
    documents/                # Source markdown files
  solar-home-improvement/
    index.db
    documents/
  healthcare-dental/
    index.db
    documents/
  legal/
    index.db
    documents/
  real-estate/
    index.db
    documents/
  general/
    index.db                  # Cross-sector marketing knowledge
    documents/
```

**Advantages:**

- Complete isolation: no chance of cross-contamination.
- Each database is small and fast (typically <50 MB per sector).
- Can use different embedding models per sector if needed.
- Easy to backup, move, or delete individual sectors.
- Simple to add new sectors: just create a new directory and database.

**Disadvantages:**

- Cross-sector queries require searching multiple databases.
- Slightly more complex routing logic.

### Option B: Single Database with Namespace/Sector Column

```sql
-- All chunks in one database, filtered by sector
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY,
    document_id INTEGER,
    content TEXT,
    embedding BLOB,
    sector TEXT NOT NULL,   -- 'smb-local-services', 'solar', 'healthcare', etc.
    ...
);

-- Queries always include sector filter
SELECT * FROM chunks WHERE sector = 'solar' AND ...
```

**Advantages:**

- Single database to manage.
- Cross-sector queries are trivial (just remove the WHERE clause).

**Disadvantages:**

- Sector filter must be applied to every query (easy to forget).
- Vector search in sqlite-vec does not support pre-filtering efficiently -- it scans all vectors then filters, which is slower for large datasets.
- All sectors share the same embedding model and dimensions.

**Recommendation:** Use Option A (separate databases) for OpenClaw. The isolation benefits outweigh the minor routing complexity. Reserve Option B for the Qdrant production deployment where collection-level separation is already built in.

---

## Sectors to Build

### Priority 1 -- Build Now (Existing Client Verticals)

#### 1. SMB Local Services
- **Businesses:** Plumbers, HVAC technicians, electricians, roofers, landscapers, house cleaners, painters, pest control, garage door companies
- **Knowledge needed:** Channel effectiveness (GBP, Local SEO, LSA, Facebook), typical budgets ($2K-5K/mo), seasonal patterns, tech stacks (Jobber, ServiceTitan, GHL), compliance (licensing, insurance)
- **Size estimate:** 500-1,000 chunks
- **Detailed file:** `sector-knowledge/smb-local-services.md`

#### 2. Solar and Home Improvement
- **Businesses:** Solar installers, window/siding companies, roofing, general remodelers, HVAC installation
- **Knowledge needed:** Lead sources (Angi, HomeAdvisor, canvassing), deal sizes ($15K-40K), sales cycles (30-90 days), financing (ITC, PACE, PPA), permitting
- **Size estimate:** 500-800 chunks
- **Detailed file:** `sector-knowledge/solar-home-improvement.md`

### Priority 2 -- Build Next (Expansion Verticals)

#### 3. Healthcare / Dental
- **Businesses:** Dental practices, med spas, chiropractors, optometrists, dermatologists
- **Knowledge needed:** Patient acquisition costs ($200-500/new patient), HIPAA compliance, review management, insurance networks, seasonal patterns (back-to-school dental, New Year med spa)
- **Size estimate:** 400-700 chunks

#### 4. Legal (Personal Injury, Family Law)
- **Businesses:** Personal injury attorneys, family law firms, criminal defense, estate planning
- **Knowledge needed:** Case value economics, PPC costs ($50-200/click for PI), LSA for lawyers, bar advertising rules, intake optimization
- **Size estimate:** 400-600 chunks

#### 5. Real Estate
- **Businesses:** Real estate agents, brokerages, property management companies, mortgage brokers
- **Knowledge needed:** Lead gen (Zillow, Realtor.com, Facebook), nurture sequences, market cycle sensitivity, licensing/CE requirements, IDX websites
- **Size estimate:** 400-600 chunks

### Always Present -- Cross-Sector General Knowledge

#### General Marketing Knowledge Base
- **Contents:** SEO fundamentals, Google Ads best practices, Facebook/Meta advertising, email marketing, CRM usage, analytics/tracking, conversion optimization, brand strategy
- **Purpose:** Provides foundational marketing knowledge that applies across all industries
- **Size estimate:** 1,000-2,000 chunks
- **Search behavior:** Always included as a fallback when sector-specific results are insufficient

---

## Agent Routing: Query to Sector

When a query comes in, the agent must determine which sector knowledge base(s) to search.

### Routing Strategy

```python
from enum import Enum
from typing import Optional

class Sector(Enum):
    SMB_LOCAL = "smb-local-services"
    SOLAR_HOME = "solar-home-improvement"
    HEALTHCARE = "healthcare-dental"
    LEGAL = "legal"
    REAL_ESTATE = "real-estate"
    GENERAL = "general"

class SectorRouter:
    """Route queries to the appropriate sector knowledge base(s)."""

    # Keywords that strongly indicate a sector
    SECTOR_KEYWORDS = {
        Sector.SMB_LOCAL: [
            "plumber", "plumbing", "hvac", "electrician", "landscap",
            "roofing", "roofer", "cleaning", "cleaner", "painter",
            "pest control", "garage door", "handyman", "contractor",
            "home service", "local service", "service area",
        ],
        Sector.SOLAR_HOME: [
            "solar", "panel", "inverter", "itc", "tax credit",
            "window", "siding", "remodel", "home improvement",
            "enphase", "solaredge", "aurora", "canvassing",
            "pace financing", "ppa", "net metering",
        ],
        Sector.HEALTHCARE: [
            "dental", "dentist", "medical", "healthcare", "patient",
            "hipaa", "med spa", "chiropractic", "optometrist",
            "dermatolog", "practice", "provider",
        ],
        Sector.LEGAL: [
            "attorney", "lawyer", "law firm", "legal", "personal injury",
            "family law", "criminal defense", "estate planning",
            "bar", "case value", "intake", "settlement",
        ],
        Sector.REAL_ESTATE: [
            "real estate", "realtor", "broker", "property",
            "zillow", "mls", "idx", "listing", "mortgage",
            "home buyer", "home seller",
        ],
    }

    def route(
        self,
        query: str,
        client_sector: Optional[Sector] = None,
        include_general: bool = True,
    ) -> list[Sector]:
        """
        Determine which sector(s) to search.

        Args:
            query: The user's search query.
            client_sector: If known, the client's industry (highest priority).
            include_general: Whether to always include the general knowledge base.

        Returns:
            Ordered list of sectors to search.
        """
        sectors = []

        # Priority 1: Explicit client sector (if known)
        if client_sector:
            sectors.append(client_sector)

        # Priority 2: Keyword detection
        query_lower = query.lower()
        for sector, keywords in self.SECTOR_KEYWORDS.items():
            if sector in sectors:
                continue
            for keyword in keywords:
                if keyword in query_lower:
                    sectors.append(sector)
                    break

        # Priority 3: Always include general as fallback
        if include_general and Sector.GENERAL not in sectors:
            sectors.append(Sector.GENERAL)

        # If nothing detected, search general only
        if not sectors:
            sectors = [Sector.GENERAL]

        return sectors

    def search_all_sectors(
        self,
        query: str,
        sectors: list[Sector],
        limit_per_sector: int = 5,
    ) -> list[dict]:
        """
        Search across multiple sector databases and merge results.

        Each sector's results are independently ranked, then interleaved
        with a preference for the primary (first) sector.
        """
        all_results = []
        for i, sector in enumerate(sectors):
            # Primary sector gets more results
            limit = limit_per_sector * 2 if i == 0 else limit_per_sector
            db_path = f"~/.openclaw/memory/knowledge/{sector.value}/index.db"
            results = hybrid_search(db_path, query, limit=limit)
            for r in results:
                r["sector"] = sector.value
                r["sector_priority"] = i
            all_results.extend(results)

        # Sort: primary sector first, then by RRF score
        all_results.sort(key=lambda r: (r["sector_priority"], -r["rrf_score"]))
        return all_results
```

### Routing Examples

| Query | Detected Sectors | Reason |
|-------|-----------------|--------|
| "What's the best way to get more calls for a plumber?" | SMB Local, General | "plumber" keyword detected |
| "How much does a solar lead cost?" | Solar/Home, General | "solar" + "lead" keywords |
| "Best Facebook ad strategy" | General only | No sector-specific keywords |
| "HIPAA compliance for marketing" | Healthcare, General | "HIPAA" keyword |
| (Client is known to be a roofer) + "improve my close rate" | SMB Local, General | Client sector takes priority |

---

## Knowledge Base Content Per Sector

Each sector knowledge base should contain these categories of content:

### 1. Pain Points Catalog
Documented pain points that businesses in this sector commonly experience, phrased the way business owners actually say them. Used for outreach personalization and conversation context.

### 2. Solutions Library
Proven marketing solutions mapped to each pain point. "If they say X, recommend Y."

### 3. Pricing Benchmarks
Average marketing budgets, cost per lead, cost per acquisition, average deal size, LTV. Updated at least quarterly.

### 4. Case Studies
Before/after narratives showing measurable results. Structure: situation, action, result, with specific numbers.

### 5. Compliance Requirements
Industry-specific regulations that affect marketing: licensing, advertising rules, required disclosures, privacy laws.

### 6. Marketing Channel Effectiveness
Ranked channels by ROI for this sector with typical performance metrics (CPL, conversion rate, ROAS).

### 7. Seasonal Patterns
Month-by-month demand patterns that affect marketing timing and budget allocation.

### 8. Tech Stack Intelligence
Common software tools used by businesses in this sector. Important for integration conversations and identifying upsell opportunities.

### 9. Competitor Landscape
Major competitors (both local and national), their positioning, and how to differentiate.

### 10. Outreach Templates
Pre-written email, DM, and call scripts customized for this sector's pain points and language.

---

## Maintenance Plan

### Update Frequency

| Content Type | Update Frequency | Source |
|-------------|-----------------|--------|
| Pain points | Quarterly | Sales call recordings, client feedback |
| Pricing benchmarks | Quarterly | Industry reports, internal data |
| Case studies | Monthly | Completed client campaigns |
| Compliance | Semi-annually | Legal review, regulation changes |
| Channel effectiveness | Quarterly | Campaign performance data |
| Seasonal patterns | Annually | Historical data analysis |
| Tech stack | Semi-annually | Market research |
| Outreach templates | Monthly | A/B test results |

### Update Process

1. **Source new content:** Collect updated data from sales calls, campaign results, industry reports.
2. **Format as markdown:** Write or update the relevant markdown files in the sector's `documents/` folder.
3. **Re-ingest:** Run the ingestion pipeline (see `knowledge-ingestion.md`) on changed files only. The content hash check ensures only modified documents are re-processed.
4. **Verify:** Run a few test queries to confirm the new content appears in search results.
5. **Log:** Record the update in the daily log for audit trail.

---

## Cross-Sector Insights

Some patterns emerge across multiple industries. These belong in the general knowledge base:

- **Seasonal budget allocation:** Most SMBs increase marketing spend in Q1 (new year resolutions) and reduce in Q4 (holiday distraction). This applies across plumbing, dental, legal, and real estate.
- **Review velocity matters everywhere:** Whether it's Google reviews for a plumber or Healthgrades for a dentist, recent positive reviews correlate with conversion rate across all sectors.
- **GBP optimization is universal:** Google Business Profile optimization is the single highest-ROI activity for any local business, regardless of industry.
- **Follow-up speed wins:** The first company to respond to a lead within 5 minutes wins the job 50%+ of the time. This holds across every sector.
- **The "3-pack" effect:** Appearing in Google's local 3-pack doubles click-through rates for any local service business.

These cross-sector insights should be stored in the general knowledge base and surfaced alongside sector-specific results.

---

## Integration with Rise Local Pipeline

The multi-sector RAG system connects to Rise Local's 15-signal pain scoring:

```
Rise Local Pain Scoring (15 signals)
  -> Identifies businesses with specific pain points
  -> Enriches lead record with detected pain points
  -> Routes to appropriate sector knowledge base
  -> RAG retrieves relevant solutions, case studies, outreach templates
  -> Agent generates personalized outreach using sector-specific context
```

**Example flow:**

1. Rise Local scores "ABC Plumbing" with pain signals: low Google review count (3.2 stars), no Google Ads running, website not mobile-friendly.
2. Lead is tagged as sector: `smb-local-services`, sub-sector: `plumbing`.
3. Outreach agent queries the SMB Local Services knowledge base: "solutions for plumber with low review count and no Google Ads."
4. RAG returns: relevant case study (similar plumber, went from 3.1 to 4.6 stars in 90 days), recommended action plan, outreach template.
5. Agent personalizes the template with ABC Plumbing's specific details and sends the outreach.

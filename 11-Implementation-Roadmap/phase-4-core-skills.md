# Phase 4 - Core Skills (Week 3-4)

## Goal

Build the three most valuable skills for OpenClaw: CRM management via GoHighLevel, lead enrichment via Clay.com and supporting APIs, and presentation generation. By the end of this phase, you can manage your CRM, enrich leads, and generate client-ready presentations using natural language commands.

---

## Skill Architecture Recap

Each OpenClaw skill follows this structure:
- **Trigger**: Natural language intent or explicit command
- **Input validation**: Check required parameters
- **Execution**: API calls, data processing, file generation
- **Output**: Structured response, created/updated records, generated files
- **HITL gates**: Approval required for sensitive actions

---

## Day 1-3: CRM Management Skill

### Connect GHL MCP Server to OpenClaw

Your existing GHL MCP is already configured in your Claude Code environment. Now connect it to OpenClaw.

```bash
# Create skill directory
mkdir -p ~/.openclaw/skills/crm-management

# Create the GHL connection configuration
cat > ~/.openclaw/skills/crm-management/config.json << 'JSON'
{
  "skill_name": "crm-management",
  "description": "Manage GoHighLevel CRM: contacts, pipelines, opportunities, conversations",
  "version": "1.0.0",
  "dependencies": {
    "api": "ghl",
    "env_vars": ["GHL_API_KEY", "GHL_LOCATION_ID"]
  },
  "capabilities": [
    {
      "name": "create_contact",
      "description": "Create a new contact in GHL",
      "hitl_required": false,
      "params": ["name", "email", "phone", "company", "tags"]
    },
    {
      "name": "update_contact",
      "description": "Update an existing contact",
      "hitl_required": "when changing email or phone",
      "params": ["contact_id", "fields_to_update"]
    },
    {
      "name": "delete_contact",
      "description": "Delete a contact from GHL",
      "hitl_required": true,
      "params": ["contact_id"]
    },
    {
      "name": "search_contacts",
      "description": "Search contacts by name, email, phone, or tags",
      "hitl_required": false,
      "params": ["query", "filters"]
    },
    {
      "name": "list_pipeline",
      "description": "List all opportunities in a pipeline",
      "hitl_required": false,
      "params": ["pipeline_id", "stage_filter"]
    },
    {
      "name": "create_opportunity",
      "description": "Create a new opportunity/deal",
      "hitl_required": false,
      "params": ["contact_id", "pipeline_id", "stage", "value", "name"]
    },
    {
      "name": "move_opportunity",
      "description": "Move an opportunity to a different pipeline stage",
      "hitl_required": false,
      "params": ["opportunity_id", "new_stage"]
    },
    {
      "name": "add_note",
      "description": "Add a note to a contact",
      "hitl_required": false,
      "params": ["contact_id", "note_content"]
    },
    {
      "name": "bulk_update",
      "description": "Update multiple contacts at once",
      "hitl_required": true,
      "params": ["contact_ids", "fields_to_update"]
    },
    {
      "name": "pipeline_report",
      "description": "Generate a pipeline status report",
      "hitl_required": false,
      "params": ["pipeline_id", "date_range"]
    }
  ]
}
JSON
```

### Build the CRM Skill Handler

```bash
cat > ~/.openclaw/skills/crm-management/handler.js << 'JS'
/**
 * CRM Management Skill for OpenClaw
 * Interfaces with GoHighLevel API via MCP
 */

const GHL_BASE_URL = 'https://services.leadconnectorhq.com';

// Helper: Make authenticated GHL API request
async function ghlRequest(method, endpoint, body = null) {
  const options = {
    method,
    headers: {
      'Authorization': `Bearer ${process.env.GHL_API_KEY}`,
      'Content-Type': 'application/json',
      'Version': '2021-07-28'
    }
  };
  if (body) options.body = JSON.stringify(body);

  const response = await fetch(`${GHL_BASE_URL}${endpoint}`, options);
  if (!response.ok) {
    throw new Error(`GHL API error: ${response.status} ${await response.text()}`);
  }
  return response.json();
}

// Create a new contact
async function createContact({ name, email, phone, company, tags = [] }) {
  const [firstName, ...lastParts] = name.split(' ');
  const lastName = lastParts.join(' ');

  const contact = await ghlRequest('POST', '/contacts/', {
    locationId: process.env.GHL_LOCATION_ID,
    firstName,
    lastName,
    email,
    phone,
    companyName: company,
    tags
  });

  return {
    success: true,
    contact_id: contact.contact.id,
    message: `Created contact: ${name} (${email}) with ID ${contact.contact.id}`
  };
}

// Search contacts
async function searchContacts({ query, filters = {} }) {
  const params = new URLSearchParams({
    locationId: process.env.GHL_LOCATION_ID,
    query,
    limit: filters.limit || 20
  });

  const results = await ghlRequest('GET', `/contacts/?${params}`);
  return {
    success: true,
    count: results.contacts.length,
    contacts: results.contacts.map(c => ({
      id: c.id,
      name: `${c.firstName} ${c.lastName}`,
      email: c.email,
      phone: c.phone,
      company: c.companyName,
      tags: c.tags
    }))
  };
}

// Create opportunity in pipeline
async function createOpportunity({ contact_id, pipeline_id, stage, value, name }) {
  const opp = await ghlRequest('POST', '/opportunities/', {
    locationId: process.env.GHL_LOCATION_ID,
    contactId: contact_id,
    pipelineId: pipeline_id,
    pipelineStageId: stage,
    monetaryValue: value,
    name
  });

  return {
    success: true,
    opportunity_id: opp.opportunity.id,
    message: `Created opportunity: ${name} ($${value}) in pipeline`
  };
}

// Generate pipeline report
async function pipelineReport({ pipeline_id, date_range }) {
  const pipelines = await ghlRequest('GET',
    `/opportunities/pipelines/${pipeline_id}?locationId=${process.env.GHL_LOCATION_ID}`
  );

  // Aggregate by stage
  const stages = {};
  for (const stage of pipelines.stages || []) {
    stages[stage.name] = {
      count: stage.count || 0,
      value: stage.totalValue || 0
    };
  }

  return {
    success: true,
    pipeline_name: pipelines.name,
    stages,
    total_opportunities: Object.values(stages).reduce((sum, s) => sum + s.count, 0),
    total_value: Object.values(stages).reduce((sum, s) => sum + s.value, 0)
  };
}

module.exports = {
  createContact,
  searchContacts,
  createOpportunity,
  pipelineReport
};
JS
```

### Test CRM Skill Scenarios

```bash
# Test: Create a contact
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a contact for John Smith at ABC Plumbing, email john@abcplumbing.com, phone 512-555-1234, tag as prospect"}'

# Expected: Agent creates contact in GHL, returns contact ID

# Test: Search contacts
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find all contacts tagged as prospect in GHL"}'

# Test: Pipeline operations
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me the current pipeline status - how many deals in each stage?"}'

# Test: Complex multi-step
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a contact for Jane Doe at Sunshine Solar, add her as an opportunity worth $3000 in the new leads pipeline stage"}'
```

### Implement HITL for Destructive Operations

Verify that these operations trigger approval requests:

```bash
# Test: Delete should require approval
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Delete the contact John Smith from GHL"}'
# Expected: Telegram notification asking for approval

# Test: Bulk update should require approval
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tag all contacts from Austin, TX as local-prospect"}'
# Expected: Telegram notification with count and details
```

---

## Day 4-6: Lead Enrichment Skill

### Connect Clay.com API

```bash
mkdir -p ~/.openclaw/skills/lead-enrichment

cat > ~/.openclaw/skills/lead-enrichment/config.json << 'JSON'
{
  "skill_name": "lead-enrichment",
  "description": "Enrich business leads using waterfall enrichment strategy",
  "version": "1.0.0",
  "dependencies": {
    "apis": ["clay", "google_places", "zerobounce"],
    "env_vars": ["CLAY_API_KEY", "ZEROBOUNCE_API_KEY"]
  },
  "enrichment_waterfall": [
    {
      "step": 1,
      "source": "google_places",
      "fields": ["business_name", "address", "phone", "website", "rating", "reviews_count", "hours"],
      "cost_per_lookup": 0.00,
      "notes": "Free tier available, start here"
    },
    {
      "step": 2,
      "source": "website_scrape",
      "fields": ["tech_stack", "has_chat_widget", "has_booking", "page_speed", "mobile_friendly", "ssl"],
      "cost_per_lookup": 0.00,
      "notes": "Built-in Playwright scraping, free"
    },
    {
      "step": 3,
      "source": "clay_enrichment",
      "fields": ["owner_name", "owner_email", "owner_linkedin", "employee_count", "revenue_estimate", "founded_year"],
      "cost_per_lookup": 0.05,
      "notes": "Clay credits, most expensive step"
    },
    {
      "step": 4,
      "source": "zerobounce",
      "fields": ["email_valid", "email_quality_score", "catch_all"],
      "cost_per_lookup": 0.01,
      "notes": "Only run on emails found in step 3"
    }
  ],
  "scoring": {
    "signals": [
      {"name": "has_website", "weight": 5, "source": "google_places"},
      {"name": "website_outdated", "weight": 10, "source": "website_scrape", "condition": "no mobile responsive or slow speed"},
      {"name": "no_chat_widget", "weight": 8, "source": "website_scrape"},
      {"name": "no_online_booking", "weight": 8, "source": "website_scrape"},
      {"name": "low_google_reviews", "weight": 7, "source": "google_places", "condition": "reviews < 20"},
      {"name": "low_rating", "weight": 6, "source": "google_places", "condition": "rating < 4.0"},
      {"name": "no_ssl", "weight": 5, "source": "website_scrape"},
      {"name": "no_google_ads", "weight": 4, "source": "website_scrape"},
      {"name": "small_team", "weight": 3, "source": "clay", "condition": "employees < 10"},
      {"name": "email_valid", "weight": 10, "source": "zerobounce", "condition": "valid email found"},
      {"name": "owner_linkedin_found", "weight": 5, "source": "clay"},
      {"name": "high_revenue_estimate", "weight": 4, "source": "clay", "condition": "revenue > 500K"},
      {"name": "recently_founded", "weight": 2, "source": "clay", "condition": "founded < 3 years ago"},
      {"name": "no_social_media", "weight": 3, "source": "website_scrape"},
      {"name": "competitor_uses_agency", "weight": 6, "source": "website_scrape", "condition": "detected marketing agency footer"}
    ],
    "tiers": {
      "hot": {"min_score": 70, "action": "immediate_outreach"},
      "warm": {"min_score": 40, "action": "nurture_sequence"},
      "cold": {"min_score": 0, "action": "database_only"}
    }
  },
  "cost_tracking": {
    "enabled": true,
    "daily_budget": 25.00,
    "alert_at_80_percent": true,
    "pause_at_100_percent": true
  }
}
JSON
```

### Build Enrichment Skill Handler

```bash
cat > ~/.openclaw/skills/lead-enrichment/handler.js << 'JS'
/**
 * Lead Enrichment Skill for OpenClaw
 * Waterfall enrichment: Google Places -> Website Scrape -> Clay -> ZeroBounce
 */

// Step 1: Google Places lookup
async function enrichFromGooglePlaces(businessName, location) {
  const query = encodeURIComponent(`${businessName} ${location}`);
  // Use Google Places API (Text Search)
  const response = await fetch(
    `https://maps.googleapis.com/maps/api/place/textsearch/json?query=${query}&key=${process.env.GOOGLE_PLACES_KEY}`
  );
  const data = await response.json();

  if (!data.results || data.results.length === 0) {
    return { found: false };
  }

  const place = data.results[0];
  // Get details for phone and website
  const details = await fetch(
    `https://maps.googleapis.com/maps/api/place/details/json?place_id=${place.place_id}&fields=formatted_phone_number,website,opening_hours,url&key=${process.env.GOOGLE_PLACES_KEY}`
  );
  const detailData = await details.json();

  return {
    found: true,
    business_name: place.name,
    address: place.formatted_address,
    rating: place.rating,
    reviews_count: place.user_ratings_total,
    phone: detailData.result?.formatted_phone_number,
    website: detailData.result?.website,
    google_maps_url: detailData.result?.url
  };
}

// Step 2: Website analysis (uses Playwright via OpenClaw)
async function analyzeWebsite(websiteUrl) {
  if (!websiteUrl) return { analyzed: false, reason: 'no_website' };

  // This would call OpenClaw's built-in browser tool
  const analysis = {
    url: websiteUrl,
    has_ssl: websiteUrl.startsWith('https'),
    // These would be populated by actual Playwright analysis:
    mobile_friendly: null,
    page_speed_score: null,
    has_chat_widget: null,
    has_booking: null,
    has_social_links: null,
    tech_stack: [],
    detected_agency: null
  };

  return analysis;
}

// Step 3: Clay enrichment
async function enrichFromClay(businessName, website, location) {
  const response = await fetch('https://api.clay.com/v1/enrich', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.CLAY_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      company_name: businessName,
      company_domain: website ? new URL(website).hostname : undefined,
      company_location: location
    })
  });

  const data = await response.json();
  return {
    owner_name: data.owner_name,
    owner_email: data.owner_email,
    owner_linkedin: data.owner_linkedin_url,
    employee_count: data.employee_count,
    revenue_estimate: data.revenue_estimate,
    founded_year: data.founded_year,
    credits_used: data.credits_consumed || 1
  };
}

// Step 4: Email verification
async function verifyEmail(email) {
  if (!email) return { verified: false, reason: 'no_email' };

  const response = await fetch(
    `https://api.zerobounce.net/v2/validate?api_key=${process.env.ZEROBOUNCE_API_KEY}&email=${encodeURIComponent(email)}`
  );
  const data = await response.json();

  return {
    verified: true,
    status: data.status,  // valid, invalid, catch-all, unknown
    quality_score: data.zb_score,
    is_valid: data.status === 'valid',
    is_catch_all: data.status === 'catch-all'
  };
}

// Calculate lead score based on all enrichment data
function calculateLeadScore(enrichmentData) {
  let score = 0;
  const signals = [];

  // Score based on enrichment results
  if (enrichmentData.google?.found) {
    if (!enrichmentData.google.website) { score += 5; signals.push('no_website'); }
    if (enrichmentData.google.reviews_count < 20) { score += 7; signals.push('low_reviews'); }
    if (enrichmentData.google.rating < 4.0) { score += 6; signals.push('low_rating'); }
  }

  if (enrichmentData.website?.analyzed) {
    if (!enrichmentData.website.has_ssl) { score += 5; signals.push('no_ssl'); }
    if (!enrichmentData.website.has_chat_widget) { score += 8; signals.push('no_chat'); }
    if (!enrichmentData.website.has_booking) { score += 8; signals.push('no_booking'); }
    if (!enrichmentData.website.mobile_friendly === false) { score += 10; signals.push('not_mobile_friendly'); }
  }

  if (enrichmentData.clay) {
    if (enrichmentData.clay.employee_count < 10) { score += 3; signals.push('small_team'); }
    if (enrichmentData.clay.owner_linkedin) { score += 5; signals.push('linkedin_found'); }
  }

  if (enrichmentData.email?.is_valid) { score += 10; signals.push('valid_email'); }

  // Determine tier
  let tier = 'cold';
  if (score >= 70) tier = 'hot';
  else if (score >= 40) tier = 'warm';

  return { score, tier, signals };
}

// Main enrichment pipeline
async function enrichLead(businessName, location, options = {}) {
  const results = { business_name: businessName, location };
  let totalCost = 0;

  // Step 1: Google Places (free)
  results.google = await enrichFromGooglePlaces(businessName, location);

  // Step 2: Website analysis (free)
  if (results.google.website) {
    results.website = await analyzeWebsite(results.google.website);
  }

  // Step 3: Clay enrichment (costs credits)
  if (options.include_clay !== false) {
    results.clay = await enrichFromClay(businessName, results.google?.website, location);
    totalCost += results.clay.credits_used * 0.05;
  }

  // Step 4: Email verification (costs credits)
  if (results.clay?.owner_email) {
    results.email = await verifyEmail(results.clay.owner_email);
    totalCost += 0.01;
  }

  // Calculate score
  results.scoring = calculateLeadScore(results);
  results.enrichment_cost = totalCost;

  return results;
}

module.exports = { enrichLead, calculateLeadScore };
JS
```

### Test End-to-End Enrichment

```bash
# Test single lead enrichment
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Enrich this lead: Roto-Rooter Plumbing in Austin, TX. Show me all the data you find and the lead score."}'

# Expected: Full enrichment with score and tier

# Test with cost tracking
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my current enrichment spend today? How many credits have I used?"}'

# Test batch enrichment (should trigger HITL if over budget)
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Enrich the top 20 plumbing businesses in Austin, TX. Show me the hot leads."}'
# Expected: HITL approval request (estimated cost > $5)
```

---

## Day 7-9: Presentation Generation Skill

### Set Up Presentation Environment

```bash
mkdir -p ~/.openclaw/skills/presentation-gen
mkdir -p ~/.openclaw/assets/templates/presentations

# If using python-pptx, ensure Python is available in the Docker container
# or create a sidecar container for Python operations

cat > ~/.openclaw/skills/presentation-gen/config.json << 'JSON'
{
  "skill_name": "presentation-gen",
  "description": "Generate PowerPoint presentations from natural language or data",
  "version": "1.0.0",
  "dependencies": {
    "python": ["python-pptx", "matplotlib", "Pillow"],
    "templates": "/app/assets/templates/presentations"
  },
  "templates": [
    {
      "name": "pitch_deck",
      "description": "New client pitch deck (10-12 slides)",
      "slides": ["title", "problem", "solution", "services", "process", "case_studies", "pricing", "team", "next_steps", "contact"]
    },
    {
      "name": "monthly_report",
      "description": "Monthly client performance report (8-10 slides)",
      "slides": ["title", "executive_summary", "traffic_metrics", "lead_metrics", "campaign_performance", "seo_progress", "social_metrics", "recommendations", "next_month"]
    },
    {
      "name": "strategy_proposal",
      "description": "Marketing strategy proposal (12-15 slides)",
      "slides": ["title", "executive_summary", "current_state", "market_analysis", "competitor_analysis", "strategy_overview", "channel_plan", "content_plan", "timeline", "budget", "expected_results", "team", "next_steps"]
    },
    {
      "name": "competitor_report",
      "description": "Competitive intelligence report (6-8 slides)",
      "slides": ["title", "overview", "competitor_profiles", "comparison_matrix", "gaps_opportunities", "recommendations"]
    }
  ],
  "output": {
    "format": "pptx",
    "directory": "/app/assets/generated",
    "naming": "{template}_{client}_{date}.pptx"
  }
}
JSON
```

### Create Presentation Template (Python Script)

```bash
cat > ~/.openclaw/skills/presentation-gen/generate.py << 'PYTHON'
"""
Presentation Generator for OpenClaw
Generates .pptx files from structured data using python-pptx
"""
import json
import sys
from datetime import datetime
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN


def create_slide(prs, layout_index, title, content=None, bullets=None):
    """Create a slide with title and optional content."""
    slide_layout = prs.slide_layouts[layout_index]
    slide = prs.slides.add_slide(slide_layout)

    # Set title
    if slide.shapes.title:
        slide.shapes.title.text = title

    # Set body content
    if bullets and len(slide.placeholders) > 1:
        body = slide.placeholders[1]
        tf = body.text_frame
        tf.clear()
        for i, bullet in enumerate(bullets):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = bullet
            p.font.size = Pt(18)
            p.space_after = Pt(8)

    return slide


def generate_pitch_deck(data):
    """Generate a new client pitch deck."""
    prs = Presentation()

    # Title slide
    create_slide(prs, 0, data.get('title', 'Marketing Strategy'),
                 bullets=[data.get('subtitle', 'Prepared by OnTrack Marketing')])

    # Problem slide
    create_slide(prs, 1, 'The Challenge',
                 bullets=data.get('problems', [
                     'Inconsistent lead flow',
                     'Outdated online presence',
                     'Competitors ranking higher on Google',
                     'No system for tracking ROI'
                 ]))

    # Solution slide
    create_slide(prs, 1, 'Our Solution',
                 bullets=data.get('solutions', [
                     'Data-driven digital marketing strategy',
                     'Modern, mobile-first website',
                     'Local SEO domination',
                     'Automated lead capture and nurturing'
                 ]))

    # Services slide
    create_slide(prs, 1, 'Services We Provide',
                 bullets=data.get('services', [
                     'Website Design & Development',
                     'Search Engine Optimization (SEO)',
                     'Google Ads Management',
                     'Social Media Marketing',
                     'Reputation Management',
                     'CRM Setup & Automation'
                 ]))

    # Process slide
    create_slide(prs, 1, 'Our Process',
                 bullets=[
                     '1. Discovery: Understand your business and goals',
                     '2. Strategy: Build a custom marketing plan',
                     '3. Execute: Launch campaigns across channels',
                     '4. Optimize: Data-driven improvements monthly',
                     '5. Report: Transparent monthly performance reviews'
                 ])

    # Pricing slide
    create_slide(prs, 1, 'Investment',
                 bullets=data.get('pricing', [
                     'Starter: $1,500/month - SEO + Google Ads',
                     'Growth: $2,500/month - Full digital marketing',
                     'Premium: $4,000/month - Complete marketing partner',
                     'All plans include monthly reporting and strategy calls'
                 ]))

    # Next Steps slide
    create_slide(prs, 1, 'Next Steps',
                 bullets=[
                     'Schedule a 30-minute strategy call',
                     'We will present a custom marketing audit',
                     'Choose the plan that fits your goals',
                     'Launch within 2 weeks of signing'
                 ])

    # Contact slide
    create_slide(prs, 0, 'Let\'s Grow Your Business',
                 bullets=[data.get('contact_info', 'contact@ontrackmarketing.com')])

    return prs


def generate_monthly_report(data):
    """Generate a monthly client performance report."""
    prs = Presentation()

    client = data.get('client_name', 'Client')
    month = data.get('month', datetime.now().strftime('%B %Y'))

    # Title
    create_slide(prs, 0, f'{client} - Monthly Report', bullets=[month])

    # Executive Summary
    create_slide(prs, 1, 'Executive Summary',
                 bullets=data.get('summary', [
                     'Overall performance on track',
                     'Key metrics improved month-over-month'
                 ]))

    # Lead Metrics
    leads = data.get('leads', {})
    create_slide(prs, 1, 'Lead Generation',
                 bullets=[
                     f"Total Leads: {leads.get('total', 'N/A')}",
                     f"Qualified Leads: {leads.get('qualified', 'N/A')}",
                     f"Cost Per Lead: ${leads.get('cpl', 'N/A')}",
                     f"Conversion Rate: {leads.get('conversion_rate', 'N/A')}%",
                     f"Month-over-Month Change: {leads.get('mom_change', 'N/A')}%"
                 ])

    # Recommendations
    create_slide(prs, 1, 'Recommendations for Next Month',
                 bullets=data.get('recommendations', [
                     'Increase Google Ads budget by 15%',
                     'Add 3 new blog posts targeting long-tail keywords',
                     'Launch review request campaign'
                 ]))

    return prs


def main():
    """Main entry point - reads JSON input, generates presentation."""
    if len(sys.argv) < 2:
        print("Usage: python generate.py <input.json>")
        sys.exit(1)

    with open(sys.argv[1], 'r') as f:
        input_data = json.load(f)

    template = input_data.get('template', 'pitch_deck')
    output_path = input_data.get('output_path', f'/app/assets/generated/{template}_{datetime.now().strftime("%Y%m%d")}.pptx')

    generators = {
        'pitch_deck': generate_pitch_deck,
        'monthly_report': generate_monthly_report,
    }

    generator = generators.get(template)
    if not generator:
        print(f"Unknown template: {template}")
        sys.exit(1)

    prs = generator(input_data.get('data', {}))
    prs.save(output_path)
    print(json.dumps({'success': True, 'output_path': output_path}))


if __name__ == '__main__':
    main()
PYTHON
```

### Test Presentation Generation

```bash
# Create output directory
mkdir -p ~/.openclaw/assets/generated

# Test via natural language
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a pitch deck presentation for ABC Plumbing in Austin, TX. They have been in business for 15 years, have 12 employees, and want to grow from 30 to 50 leads per month."}'

# Test monthly report
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a monthly report presentation for ABC Plumbing for January 2026. They got 45 leads, 28 qualified, CPL was $22, conversion rate 12%, up 15% from last month."}'

# Verify file was generated
ls -la ~/.openclaw/assets/generated/
```

---

## Day 10: Integration Testing

### End-to-End Pipeline Test

Run the complete flow: discover lead, enrich, score, create CRM contact, generate presentation.

```bash
# Full pipeline test
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Run the full lead pipeline for Reliable Plumbing in Dallas, TX: 1) Enrich the lead with all available data, 2) Score them, 3) If they score warm or hot, create a contact in GHL with all enrichment data, 4) Generate an intro pitch deck customized to their situation."
  }'

# This should:
# 1. Run waterfall enrichment (Google Places -> Website -> Clay -> ZeroBounce)
# 2. Calculate lead score
# 3. Create GHL contact with enrichment data in notes
# 4. Generate a customized pitch deck .pptx file
# 5. Report back with summary and file location
```

### Verify All Three Skills Together

| Test | Command | Expected Result |
|------|---------|-----------------|
| CRM only | "List all contacts tagged prospect" | GHL search results |
| Enrichment only | "Enrich Joe's HVAC in Miami" | Full enrichment data with score |
| Presentation only | "Create a blank pitch deck" | Generated .pptx file |
| CRM + Enrichment | "Enrich and add to CRM: Smith Solar, Phoenix" | Enrichment data + new GHL contact |
| All three | "Full pipeline for Metro Dental, Chicago" | Enrichment + CRM + pitch deck |

### Document Skill Configurations

```bash
cat > ~/.openclaw/skills/SKILLS-INDEX.md << 'MD'
# OpenClaw Skills Index

## Active Skills

### 1. CRM Management (crm-management)
- **Status**: Active
- **API**: GoHighLevel
- **Capabilities**: CRUD contacts, pipeline management, notes, reports
- **HITL**: Required for delete, bulk update
- **Cost**: Free (GHL subscription already paid)

### 2. Lead Enrichment (lead-enrichment)
- **Status**: Active
- **APIs**: Google Places, Clay.com, ZeroBounce
- **Capabilities**: Waterfall enrichment, lead scoring (15 signals)
- **HITL**: Required when batch cost > $5
- **Cost**: ~$0.06 per full enrichment (Clay + ZeroBounce)

### 3. Presentation Generation (presentation-gen)
- **Status**: Active
- **Dependencies**: python-pptx, matplotlib
- **Capabilities**: Pitch decks, monthly reports, strategy proposals
- **HITL**: Not required (generates files, does not send)
- **Cost**: Free (local generation)

## Planned Skills (Phase 5+)
- Content calendar automation
- LinkedIn outreach
- Competitive intelligence
- Website generation
MD
```

---

## Success Criteria Checklist

| Criterion | Test | Status |
|-----------|------|--------|
| GHL connected to OpenClaw | Can list contacts via natural language | [ ] |
| Create contact works | "Create contact for X" creates in GHL | [ ] |
| Pipeline operations work | Can list pipeline, move opportunities | [ ] |
| HITL works for destructive CRM ops | Delete triggers Telegram approval | [ ] |
| Enrichment waterfall executes | All 4 steps run in sequence | [ ] |
| Lead scoring accurate | Scores match expected tier for test leads | [ ] |
| Cost tracking working | Can check daily enrichment spend | [ ] |
| Pitch deck generates | .pptx file created with correct content | [ ] |
| Monthly report generates | Report with actual metrics | [ ] |
| Full pipeline works | Enrich -> Score -> CRM -> Presentation | [ ] |

---

## Next Phase

With core skills working, proceed to [Phase 5 - Integrations](phase-5-integrations.md) to connect OpenClaw to your full ecosystem: n8n, Airtable, Supabase, Rise Local, Ralph, and RAFE.

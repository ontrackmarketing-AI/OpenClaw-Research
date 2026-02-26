# Phase 7 - Advanced Capabilities (Week 6-8)

## Goal

Build three high-value advanced capabilities: LinkedIn outreach with safety guardrails, competitive intelligence monitoring, and automated website generation and deployment. These move OpenClaw from an operational tool to a revenue-generating platform.

---

## Important: These Are Higher-Risk Capabilities

Each capability in this phase carries specific risks:
- **LinkedIn**: Account restrictions if done wrong (rate limits, detection)
- **Competitive intelligence**: Legal boundaries on scraping, ethical considerations
- **Website generation**: Client-facing output must be high quality

Proceed carefully, test with small batches, and use HITL aggressively until you trust the output quality.

---

## Week 1 (Day 1-5): LinkedIn Management

### LinkedIn API Access Assessment

LinkedIn has strict API access policies. Evaluate your options:

| Method | Access Level | Risk | Recommended |
|--------|-------------|------|-------------|
| LinkedIn Marketing API | Requires approved app | Low | For ad management only |
| LinkedIn Sales Navigator API | Requires Sales Nav subscription | Low | Best for lead research |
| Browser automation (Playwright) | No API needed | Medium-High | Use with extreme caution |
| LinkedIn profile data via Clay | Through Clay enrichment | Low | Already set up in Phase 4 |

**Recommended approach**: Use Clay for LinkedIn data enrichment (already done), and manual/semi-automated outreach with OpenClaw generating the messages but you sending them manually or via LinkedIn's native tools.

### Build LinkedIn Research Skill

```bash
mkdir -p ~/.openclaw/skills/linkedin-management

cat > ~/.openclaw/skills/linkedin-management/config.json << 'JSON'
{
  "skill_name": "linkedin-management",
  "description": "LinkedIn prospect research, message generation, and outreach management",
  "version": "1.0.0",
  "approach": "hybrid",
  "capabilities": [
    {
      "name": "research_prospect",
      "description": "Research a LinkedIn prospect using Clay enrichment data",
      "method": "api",
      "hitl_required": false,
      "tools": ["clay_enrichment", "rag"]
    },
    {
      "name": "generate_connection_message",
      "description": "Generate a personalized LinkedIn connection request message",
      "method": "llm",
      "hitl_required": true,
      "constraints": {
        "max_length": 300,
        "tone": "professional_friendly",
        "no_sales_pitch_in_connection": true
      }
    },
    {
      "name": "generate_followup_message",
      "description": "Generate a follow-up message after connection accepted",
      "method": "llm",
      "hitl_required": true,
      "constraints": {
        "max_length": 500,
        "tone": "value_first",
        "include_relevant_insight": true
      }
    },
    {
      "name": "generate_inmail",
      "description": "Generate an InMail for prospects not yet connected",
      "method": "llm",
      "hitl_required": true,
      "constraints": {
        "max_length": 1000,
        "subject_line_max": 50,
        "tone": "professional_consultative"
      }
    },
    {
      "name": "track_outreach",
      "description": "Track all outreach attempts, responses, and outcomes",
      "method": "database",
      "hitl_required": false
    }
  ],
  "safety_limits": {
    "max_connections_per_day": 20,
    "max_messages_per_day": 50,
    "max_inmails_per_day": 10,
    "cooldown_between_actions_seconds": 120,
    "daily_reset_time": "00:00",
    "weekend_activity": false,
    "pause_on_linkedin_warning": true
  }
}
JSON
```

### Create Outreach Tracking Database

```sql
-- Run in Supabase SQL Editor

CREATE TABLE linkedin_outreach (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prospect_name TEXT NOT NULL,
  prospect_title TEXT,
  prospect_company TEXT,
  prospect_linkedin_url TEXT,
  prospect_industry TEXT,

  -- Enrichment data
  enrichment_data JSONB DEFAULT '{}',
  lead_score INTEGER,

  -- Outreach tracking
  connection_sent_at TIMESTAMPTZ,
  connection_message TEXT,
  connection_accepted_at TIMESTAMPTZ,

  followup_sent_at TIMESTAMPTZ,
  followup_message TEXT,
  followup_response TEXT,

  inmail_sent_at TIMESTAMPTZ,
  inmail_message TEXT,
  inmail_response TEXT,

  -- Outcome
  status TEXT DEFAULT 'identified' CHECK (status IN (
    'identified', 'connection_sent', 'connected', 'followup_sent',
    'responded', 'meeting_booked', 'converted', 'declined', 'no_response'
  )),
  outcome_notes TEXT,

  -- Metadata
  campaign TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_linkedin_status ON linkedin_outreach(status);
CREATE INDEX idx_linkedin_campaign ON linkedin_outreach(campaign);
CREATE INDEX idx_linkedin_created ON linkedin_outreach(created_at);
```

### Build Message Generation with RAG Context

The key differentiator: OpenClaw uses your industry knowledge base (Phase 3) to generate genuinely relevant messages, not generic templates.

```bash
cat > ~/.openclaw/skills/linkedin-management/message-templates.json << 'JSON'
{
  "message_strategies": {
    "connection_request": {
      "system_prompt": "You are writing a LinkedIn connection request. Rules: 1) Under 300 characters. 2) Reference something specific about their business or industry. 3) NO sales pitch. 4) Be genuine and curious. 5) End with a reason to connect, not a CTA.",
      "rag_context": "Retrieve relevant industry insights for {prospect_industry} to personalize the message",
      "examples": [
        {
          "context": "Plumbing company owner, 15 employees, no website",
          "message": "Hi {name}, I noticed {company} has strong Google reviews but no website yet. I work with local service businesses on their digital presence. Would love to connect and share some insights about what's working in the plumbing space."
        },
        {
          "context": "Solar installer, growing company, active on Facebook",
          "message": "Hi {name}, saw {company}'s recent project posts -- impressive work! I help solar companies generate more qualified leads. Always great to connect with others in the local services space."
        }
      ]
    },
    "followup_after_accept": {
      "system_prompt": "Write a follow-up message after they accepted your connection. Rules: 1) Thank them for connecting. 2) Provide genuine value (insight, stat, or resource). 3) Soft CTA for a conversation, not a sale. 4) Under 500 characters.",
      "rag_context": "Retrieve specific marketing insights and stats for {prospect_industry}",
      "send_delay_hours": 24
    },
    "inmail": {
      "system_prompt": "Write a LinkedIn InMail. Rules: 1) Subject line under 50 chars that creates curiosity. 2) Open with a specific observation about their business. 3) Share one relevant insight or stat. 4) Ask a question that opens dialogue. 5) Under 1000 characters total.",
      "rag_context": "Retrieve industry benchmarks and pain points for {prospect_industry}"
    }
  }
}
JSON
```

### Test with Small Batch

```bash
# Step 1: Research prospects
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Research 5 plumbing company owners in Austin, TX on LinkedIn. Use Clay data to find their profiles, company size, and any relevant details."}'

# Step 2: Generate personalized messages (HITL required)
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Generate personalized LinkedIn connection request messages for each of the 5 prospects. Use industry knowledge to make each message unique."}'

# Expected: Telegram notification with 5 messages for your review
# Review each message carefully
# Approve only the ones that sound natural and relevant

# Step 3: Track the outreach
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Log that I sent connection requests to all 5 Austin plumbing prospects today. Track them in the outreach database."}'

# Step 4: Check results after a few days
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me the status of my LinkedIn outreach campaign for Austin plumbers. How many accepted? Any responses?"}'
```

### Monitor for LinkedIn Warnings

```bash
cat > ~/.openclaw/skills/linkedin-management/safety-monitor.json << 'JSON'
{
  "monitoring": {
    "check_before_each_action": true,
    "rules": [
      {
        "check": "daily_connection_count",
        "limit": 20,
        "action_on_breach": "pause_and_alert"
      },
      {
        "check": "weekly_connection_count",
        "limit": 80,
        "action_on_breach": "pause_and_alert"
      },
      {
        "check": "acceptance_rate",
        "min_threshold": 0.15,
        "window_days": 7,
        "action_on_low": "reduce_daily_limit_to_10"
      },
      {
        "check": "response_rate",
        "min_threshold": 0.05,
        "window_days": 14,
        "action_on_low": "review_message_quality"
      }
    ],
    "alerts": {
      "channel": "telegram",
      "alert_on_pause": true,
      "alert_on_low_metrics": true
    }
  }
}
JSON
```

---

## Week 1-2 (Day 5-8): Competitive Intelligence

### Build Playwright Scraping Skill

```bash
mkdir -p ~/.openclaw/skills/competitor-intel

cat > ~/.openclaw/skills/competitor-intel/config.json << 'JSON'
{
  "skill_name": "competitor-intel",
  "description": "Monitor competitor websites, detect changes, generate intelligence reports",
  "version": "1.0.0",
  "capabilities": [
    {
      "name": "monitor_website",
      "description": "Scrape and snapshot a competitor website",
      "method": "playwright",
      "hitl_required": false
    },
    {
      "name": "detect_changes",
      "description": "Compare current snapshot to previous, identify changes",
      "method": "diff",
      "hitl_required": false
    },
    {
      "name": "score_change",
      "description": "Score the significance of detected changes",
      "method": "llm",
      "hitl_required": false
    },
    {
      "name": "generate_report",
      "description": "Generate a competitive intelligence report",
      "method": "llm_with_rag",
      "hitl_required": false
    },
    {
      "name": "alert_significant_change",
      "description": "Alert on high-significance competitor changes",
      "method": "notification",
      "hitl_required": false
    }
  ],
  "scraping_config": {
    "user_agent": "Mozilla/5.0 (compatible; research bot)",
    "respect_robots_txt": true,
    "request_delay_ms": 2000,
    "max_pages_per_site": 20,
    "timeout_ms": 30000,
    "capture": ["text_content", "meta_tags", "headings", "links", "images", "structured_data"]
  },
  "legal_notes": [
    "Only scrape publicly available information",
    "Respect robots.txt directives",
    "Do not attempt to bypass authentication",
    "Do not overload target servers (rate limiting enforced)",
    "Store data for competitive analysis purposes only"
  ]
}
JSON
```

### Set Up Competitor Monitoring

```bash
cat > ~/.openclaw/config/competitor-watchlist.json << 'JSON'
{
  "competitors": {
    "description": "Competitors to monitor, organized by client",
    "clients": [
      {
        "client": "example_plumber_austin",
        "industry": "plumbing",
        "location": "Austin, TX",
        "competitors": [
          {
            "name": "Competitor A Plumbing",
            "website": "https://competitora-plumbing.com",
            "monitor_pages": ["/", "/services", "/pricing", "/about"],
            "monitor_frequency": "daily"
          },
          {
            "name": "Competitor B Plumbing",
            "website": "https://competitorb-plumbing.com",
            "monitor_pages": ["/", "/services"],
            "monitor_frequency": "weekly"
          },
          {
            "name": "Competitor C Plumbing",
            "website": "https://competitorc-plumbing.com",
            "monitor_pages": ["/", "/services"],
            "monitor_frequency": "weekly"
          }
        ]
      }
    ]
  },
  "change_scoring": {
    "high_significance": [
      "pricing_change",
      "new_service_added",
      "new_location",
      "major_redesign",
      "new_promotion"
    ],
    "medium_significance": [
      "content_update",
      "new_review_response",
      "team_change",
      "testimonial_added"
    ],
    "low_significance": [
      "minor_text_edit",
      "image_swap",
      "footer_update"
    ]
  }
}
JSON
```

### Create Competitor Data Storage

```sql
-- Run in Supabase SQL Editor

CREATE TABLE competitor_snapshots (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  competitor_name TEXT NOT NULL,
  website_url TEXT NOT NULL,
  page_path TEXT NOT NULL,

  -- Snapshot data
  content_hash TEXT,
  text_content TEXT,
  meta_tags JSONB DEFAULT '{}',
  headings JSONB DEFAULT '[]',
  structured_data JSONB DEFAULT '{}',

  -- Change detection
  has_changes BOOLEAN DEFAULT false,
  changes_summary TEXT,
  change_significance TEXT CHECK (change_significance IN ('high', 'medium', 'low', 'none')),

  -- Metadata
  client TEXT,
  captured_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_competitor_name ON competitor_snapshots(competitor_name);
CREATE INDEX idx_competitor_captured ON competitor_snapshots(captured_at);
CREATE INDEX idx_competitor_significance ON competitor_snapshots(change_significance);

-- View for latest snapshots per competitor/page
CREATE VIEW latest_competitor_snapshots AS
SELECT DISTINCT ON (competitor_name, page_path)
  *
FROM competitor_snapshots
ORDER BY competitor_name, page_path, captured_at DESC;
```

### Build Change Detection Pipeline

```bash
cat > ~/.openclaw/skills/competitor-intel/change-detection.js << 'JS'
/**
 * Competitor Change Detection
 * Compares current website snapshot to previous snapshot
 */

const crypto = require('crypto');

function hashContent(text) {
  return crypto.createHash('sha256').update(text).digest('hex');
}

function detectChanges(previousSnapshot, currentSnapshot) {
  const changes = [];

  // Content hash comparison (quick check)
  if (previousSnapshot.content_hash === currentSnapshot.content_hash) {
    return { has_changes: false, changes: [] };
  }

  // Detailed diff analysis
  // Compare headings
  const prevHeadings = new Set(previousSnapshot.headings || []);
  const currHeadings = new Set(currentSnapshot.headings || []);

  for (const h of currHeadings) {
    if (!prevHeadings.has(h)) {
      changes.push({ type: 'heading_added', detail: h });
    }
  }
  for (const h of prevHeadings) {
    if (!currHeadings.has(h)) {
      changes.push({ type: 'heading_removed', detail: h });
    }
  }

  // Compare meta tags
  const prevMeta = previousSnapshot.meta_tags || {};
  const currMeta = currentSnapshot.meta_tags || {};

  if (prevMeta.title !== currMeta.title) {
    changes.push({ type: 'title_changed', detail: `"${prevMeta.title}" -> "${currMeta.title}"` });
  }
  if (prevMeta.description !== currMeta.description) {
    changes.push({ type: 'meta_description_changed', detail: 'Meta description updated' });
  }

  // Compare structured data (pricing, services)
  const prevSD = previousSnapshot.structured_data || {};
  const currSD = currentSnapshot.structured_data || {};

  if (JSON.stringify(prevSD) !== JSON.stringify(currSD)) {
    changes.push({ type: 'structured_data_changed', detail: 'Schema.org data modified' });
  }

  return {
    has_changes: changes.length > 0,
    changes,
    change_count: changes.length
  };
}

function scoreSignificance(changes) {
  const highImpact = ['pricing_change', 'new_service_added', 'structured_data_changed'];
  const medImpact = ['heading_added', 'heading_removed', 'title_changed', 'meta_description_changed'];

  let maxScore = 'low';
  for (const change of changes) {
    if (highImpact.some(h => change.type.includes(h))) maxScore = 'high';
    else if (medImpact.some(m => change.type.includes(m)) && maxScore !== 'high') maxScore = 'medium';
  }
  return maxScore;
}

module.exports = { detectChanges, scoreSignificance, hashContent };
JS
```

### Test Competitive Intelligence Pipeline

```bash
# Step 1: Initial snapshot (baseline)
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Take a baseline snapshot of competitor websites for the Austin plumber watchlist. Store in Supabase."}'

# Step 2: Check for changes (run after a few days)
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Check all monitored competitor websites for changes since last snapshot. Report any significant changes."}'

# Step 3: Generate intelligence report
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Generate a competitive intelligence report for the Austin plumbing market. Include recent competitor changes, market trends, and recommendations for our client."}'
```

### Schedule Automated Monitoring

```bash
# Add to the Mac Mini launchd schedule
cat > ~/Library/LaunchAgents/com.openclaw.competitor-monitor.plist << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.competitor-monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/curl</string>
        <string>-X</string>
        <string>POST</string>
        <string>http://localhost:18789/api/skills/invoke</string>
        <string>-H</string>
        <string>Content-Type: application/json</string>
        <string>-d</string>
        <string>{"skill": "competitor-intel", "action": "monitor_all", "params": {"alert_on_changes": true}}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
PLIST

launchctl load ~/Library/LaunchAgents/com.openclaw.competitor-monitor.plist
```

---

## Week 2 (Day 8-12): Website Generation

### Set Up Template System

```bash
mkdir -p ~/.openclaw/skills/website-gen
mkdir -p ~/.openclaw/assets/templates/websites/{plumber,solar,dental,lawyer}

cat > ~/.openclaw/skills/website-gen/config.json << 'JSON'
{
  "skill_name": "website-gen",
  "description": "Generate complete websites from business information, with industry-specific templates",
  "version": "1.0.0",
  "framework": "astro",
  "capabilities": [
    {
      "name": "generate_website",
      "description": "Generate a complete website from business info",
      "hitl_required": true,
      "params": ["business_name", "industry", "services", "location", "contact_info", "brand_colors"]
    },
    {
      "name": "deploy_website",
      "description": "Deploy generated website to Vercel",
      "hitl_required": true,
      "params": ["site_directory", "domain"]
    },
    {
      "name": "iterate_website",
      "description": "Update existing website based on feedback",
      "hitl_required": true,
      "params": ["site_directory", "feedback"]
    },
    {
      "name": "generate_content",
      "description": "Generate page content using RAG and industry knowledge",
      "hitl_required": false,
      "params": ["industry", "page_type", "business_context"]
    }
  ],
  "templates": {
    "plumber": {
      "pages": ["home", "services", "about", "contact", "reviews", "service-areas", "blog"],
      "sections": {
        "home": ["hero", "services_overview", "why_choose_us", "reviews_carousel", "service_areas_map", "cta"],
        "services": ["service_list", "individual_service_pages", "pricing_note", "cta"],
        "about": ["company_story", "team", "certifications", "values"],
        "contact": ["contact_form", "phone", "map", "hours"]
      },
      "seo": {
        "schema_types": ["LocalBusiness", "PlumbingService", "FAQPage"],
        "meta_template": "{service} in {city}, {state} | {business_name}",
        "sitemap": true,
        "robots_txt": true
      }
    },
    "solar": {
      "pages": ["home", "services", "about", "contact", "savings-calculator", "reviews", "blog"],
      "sections": {
        "home": ["hero_with_calculator", "benefits", "process", "reviews", "financing", "cta"],
        "savings_calculator": ["interactive_calculator", "incentives", "financing_options"]
      },
      "seo": {
        "schema_types": ["LocalBusiness", "ElectricalContractor", "FAQPage"],
        "meta_template": "Solar Installation in {city}, {state} | {business_name}"
      }
    },
    "dental": {
      "pages": ["home", "services", "about", "contact", "patient-info", "reviews", "blog"],
      "seo": {
        "schema_types": ["LocalBusiness", "Dentist", "MedicalBusiness", "FAQPage"]
      }
    },
    "lawyer": {
      "pages": ["home", "practice-areas", "about", "contact", "case-results", "reviews", "blog"],
      "seo": {
        "schema_types": ["LocalBusiness", "LegalService", "Attorney", "FAQPage"]
      }
    }
  },
  "deployment": {
    "platform": "vercel",
    "build_command": "npm run build",
    "output_directory": "dist",
    "environment_variables": {
      "SITE_URL": "https://{domain}"
    }
  }
}
JSON
```

### Build Website Generation Pipeline

```bash
cat > ~/.openclaw/skills/website-gen/generator.js << 'JS'
/**
 * Website Generator for OpenClaw
 * Generates Astro-based websites from business information
 */

const fs = require('fs');
const path = require('path');

async function generateWebsite(businessInfo) {
  const {
    business_name,
    industry,
    services = [],
    location,
    contact_info,
    brand_colors = { primary: '#2563eb', secondary: '#1e40af', accent: '#f59e0b' },
    about_text,
    tagline
  } = businessInfo;

  const siteDir = `/app/assets/generated/websites/${business_name.toLowerCase().replace(/\s+/g, '-')}`;

  // Create project structure
  const dirs = [
    `${siteDir}/src/pages`,
    `${siteDir}/src/components`,
    `${siteDir}/src/layouts`,
    `${siteDir}/src/styles`,
    `${siteDir}/public`,
  ];

  for (const dir of dirs) {
    fs.mkdirSync(dir, { recursive: true });
  }

  // Generate package.json
  fs.writeFileSync(`${siteDir}/package.json`, JSON.stringify({
    name: business_name.toLowerCase().replace(/\s+/g, '-'),
    version: '1.0.0',
    scripts: {
      dev: 'astro dev',
      build: 'astro build',
      preview: 'astro preview'
    },
    dependencies: {
      'astro': '^4.0.0',
      '@astrojs/tailwind': '^5.0.0',
      'tailwindcss': '^3.4.0'
    }
  }, null, 2));

  // Generate astro.config.mjs
  fs.writeFileSync(`${siteDir}/astro.config.mjs`, `
import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  integrations: [tailwind()],
  site: 'https://${business_name.toLowerCase().replace(/\s+/g, '-')}.com',
});
`);

  // Generate pages (LLM will fill in content)
  // Each page uses the base layout and is populated with
  // industry-specific content from the RAG knowledge base

  return {
    success: true,
    site_directory: siteDir,
    pages_generated: dirs.length,
    message: `Website scaffold generated at ${siteDir}. Run content generation to populate pages.`
  };
}

async function deployToVercel(siteDir, domain) {
  // Uses Vercel CLI to deploy
  // vercel --prod --yes --token=$VERCEL_TOKEN
  return {
    success: true,
    url: `https://${domain}`,
    message: `Deployed to ${domain}`
  };
}

module.exports = { generateWebsite, deployToVercel };
JS
```

### Test Website Generation

```bash
# Test: Generate a plumber website
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Generate a complete website for Reliable Plumbing in Dallas, TX. They offer residential plumbing, commercial plumbing, and emergency services. Phone: 214-555-1234. Use blue and white branding. Include SEO optimization for local search."
  }'

# Expected: HITL approval request (client-facing output)
# Review the generated site structure and content
# Approve if quality is acceptable

# Test: Deploy (requires Vercel account and token)
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Deploy the Reliable Plumbing website to Vercel at reliable-plumbing-dallas.vercel.app"}'

# Test: Iterate based on feedback
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Update the Reliable Plumbing website: change the hero section tagline to \"Dallas Trusted Plumber Since 2005\" and add a section about their 24/7 emergency service guarantee."}'
```

---

## Week 2 (Day 12-14): Advanced Skill Polish

### Migrate Remaining Claude Code Skills

Review your existing Claude Code skills and identify any that should move to OpenClaw:

```bash
# List current Claude Code skills
# (Run from your Windows PC)
# claude skill list

# For each skill that makes sense in OpenClaw, create an equivalent:
cat > ~/.openclaw/skills/MIGRATION-TRACKER.md << 'MD'
# Claude Code Skill -> OpenClaw Migration Tracker

| Claude Code Skill | OpenClaw Equivalent | Status | Notes |
|-------------------|---------------------|--------|-------|
| CRM operations | crm-management | Migrated | Phase 4 |
| Lead enrichment | lead-enrichment | Migrated | Phase 4 |
| Presentation gen | presentation-gen | Migrated | Phase 4 |
| Content calendar | content-calendar | Migrated | Phase 5 |
| LinkedIn outreach | linkedin-management | Migrated | Phase 7 |
| Competitor research | competitor-intel | Migrated | Phase 7 |
| Website generation | website-gen | Migrated | Phase 7 |
| [other skills] | [to be determined] | Pending | Review needed |

## Skills to Keep in Claude Code
- Development-focused skills (code generation, debugging)
- One-off scripting tasks
- Skills that need direct file system access on Windows

## Decision
OpenClaw handles: client-facing, automated, scheduled, multi-step operations
Claude Code handles: development work, research, one-off tasks
MD
```

### Performance and Cost Optimization

```bash
# Review costs from all Phase 7 activities
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me a cost breakdown for all Phase 7 activities: LinkedIn outreach, competitor monitoring, and website generation. What were the API costs, and where can we optimize?"}'

# Identify which operations can use local models
curl -X POST http://localhost:18789/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Review all advanced skills and identify which LLM calls could be routed to Ollama instead of Claude API without significant quality loss."}'
```

---

## Success Criteria Checklist

| Criterion | Test | Status |
|-----------|------|--------|
| LinkedIn research works | Can find prospect data via Clay | [ ] |
| Connection messages personalized | Messages reference specific industry insights | [ ] |
| HITL on all outbound LinkedIn | Every message requires approval | [ ] |
| Safety limits enforced | Cannot exceed 20 connections/day | [ ] |
| Outreach tracked in Supabase | All activity logged with status | [ ] |
| Competitor snapshots captured | Baseline snapshots for 3-5 competitors | [ ] |
| Change detection working | Differences found between snapshots | [ ] |
| Change scoring accurate | High/medium/low significance appropriate | [ ] |
| Intel reports generated | Readable, actionable competitor report | [ ] |
| Automated monitoring scheduled | Daily 6 AM competitor checks | [ ] |
| Website scaffold generates | Complete Astro project created | [ ] |
| Content populated via RAG | Industry-specific content on all pages | [ ] |
| SEO implemented | Meta tags, structured data, sitemap | [ ] |
| Vercel deployment works | Site live at Vercel URL | [ ] |
| HITL on website deployment | Cannot deploy without approval | [ ] |
| Skills migration tracked | Migration tracker up to date | [ ] |

---

## Next Phase

With all advanced capabilities built, move to [Phase 8 - Optimization](phase-8-optimization.md) for continuous improvement of performance, cost, and reliability. Phase 8 is ongoing and never truly ends.

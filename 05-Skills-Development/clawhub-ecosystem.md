# ClawHub Ecosystem: The OpenClaw Skills Marketplace

## Overview

ClawHub is the **official marketplace and registry** for OpenClaw skills, hosting 3,000+ community-contributed skills. It functions similarly to npm for Node.js or the VS Code Extension Marketplace -- a centralized place to discover, install, rate, and contribute skills.

- **Web Interface**: Browse and search at [clawhub.openclaw.sh](https://clawhub.openclaw.sh)
- **CLI Access**: Install, update, and manage skills via `openclaw skill` commands
- **API Access**: Programmatic access for automation and CI/CD integration

---

## Browsing ClawHub

### Web Interface Features

The ClawHub website provides:

- **Search**: Full-text search across skill names, descriptions, and keywords
- **Categories**: Browse by category (see below)
- **Trending**: Skills with fastest-growing downloads in the past week/month
- **New**: Recently published skills
- **Top Rated**: Highest-rated skills by community votes
- **Collections**: Curated skill bundles for specific use cases (e.g., "SMB Marketing Stack", "Developer Toolkit")

### CLI Browsing

```bash
# Search for skills by keyword
openclaw skill search "lead enrichment"

# Search within a category
openclaw skill search --category marketing "email outreach"

# View skill details before installing
openclaw skill info @creator/skill-name

# View skill README
openclaw skill readme @creator/skill-name

# List trending skills
openclaw skill trending
```

---

## Skill Categories

ClawHub organizes skills into the following primary categories:

| Category | Description | Estimated Count | Relevance to You |
|----------|-------------|-----------------|-------------------|
| **Productivity** | Task management, note-taking, scheduling, time tracking | 400+ | Medium - Obsidian integration |
| **Development** | Code generation, testing, DevOps, deployment | 600+ | High - website building, deployment |
| **Marketing** | SEO, content creation, social media, analytics | 350+ | Very High - core business |
| **CRM** | Contact management, pipeline, sales automation | 200+ | Very High - GHL integration |
| **Data** | Enrichment, scraping, transformation, databases | 450+ | Very High - lead enrichment |
| **Communication** | Email, SMS, messaging, notifications | 300+ | High - outreach automation |
| **Automation** | Workflow orchestration, scheduling, triggers | 350+ | High - n8n integration |
| **AI/ML** | LLM utilities, RAG, embeddings, fine-tuning | 250+ | Medium - AI-powered features |
| **Finance** | Invoicing, payments, accounting, reporting | 150+ | Low - not core focus |
| **Design** | Image generation, UI/UX, presentations | 100+ | Medium - presentations |

---

## Installing Skills

### Basic Installation

```bash
# Install from ClawHub by package name
openclaw skill install @creator/skill-name

# Install a specific version
openclaw skill install @creator/skill-name@2.1.0

# Install multiple skills at once
openclaw skill install @creator/skill-a @creator/skill-b @creator/skill-c

# Install from a Git repository (not on ClawHub)
openclaw skill install https://github.com/creator/skill-repo

# Install from a local directory
openclaw skill install ./my-local-skill
```

### Post-Install Configuration

Many skills require configuration (API keys, preferences) after installation:

```bash
# Interactive configuration wizard
openclaw skill setup @creator/skill-name

# Manual configuration
openclaw skill config @creator/skill-name set API_KEY=your-key-here
openclaw skill config @creator/skill-name set REGION=us-east
```

### Dependency Resolution

When you install a skill that depends on other skills, ClawHub automatically resolves and installs dependencies:

```
Installing @creator/lead-pipeline@1.5.0...
  Resolving dependencies...
  Installing @openclaw/web-scraper@2.3.1 (dependency)
  Installing @openclaw/data-formatter@1.7.0 (dependency)
  Installing @creator/lead-pipeline@1.5.0
  Done. 3 skills installed.

  Run 'openclaw skill setup @creator/lead-pipeline' to configure.
```

---

## Top Skills Relevant to Your Use Case

### CRM Skills

| Skill | Creator | Downloads | Description | GHL Relevance |
|-------|---------|-----------|-------------|---------------|
| `@openclaw/salesforce-connector` | OpenClaw | 15K+ | Full Salesforce CRM integration | Patterns adaptable to GHL |
| `@hubspot/hubspot-skill` | HubSpot | 12K+ | Official HubSpot CRM skill | Contact/deal management patterns |
| `@community/crm-pipeline-manager` | community | 5K+ | Generic pipeline stage management | Directly applicable to GHL pipelines |
| `@community/contact-enricher` | community | 8K+ | Enrich CRM contacts with external data | Core use case for Rise Local |

**Action Items**:
- Review `@community/crm-pipeline-manager` for pipeline management patterns
- Fork `@community/contact-enricher` and adapt for GHL + Clay enrichment
- Check if anyone has built a GHL-specific skill (search: "GoHighLevel", "GHL", "HighLevel")

### Email Skills

| Skill | Creator | Downloads | Description |
|-------|---------|-----------|-------------|
| `@openclaw/email-composer` | OpenClaw | 20K+ | AI-powered email drafting with templates |
| `@openclaw/email-sender` | OpenClaw | 18K+ | Send emails via SMTP, SendGrid, Mailgun |
| `@community/cold-outreach` | community | 7K+ | Multi-touch cold email sequences |
| `@community/email-warmup` | community | 3K+ | Email warmup and deliverability management |

**Action Items**:
- Install `@openclaw/email-composer` for templated outreach emails
- Evaluate `@community/cold-outreach` for Rise Local outreach sequences
- Check if email sending can route through GHL's email system

### Web Scraping Skills

| Skill | Creator | Downloads | Description |
|-------|---------|-----------|-------------|
| `@openclaw/web-scraper` | OpenClaw | 25K+ | Playwright-based web scraping |
| `@community/serp-scraper` | community | 10K+ | Search engine results page scraping |
| `@community/gmb-scraper` | community | 4K+ | Google My Business data extraction |
| `@community/review-scraper` | community | 6K+ | Multi-platform review scraping |

**Action Items**:
- `@community/gmb-scraper` is directly useful for Rise Local business discovery
- `@community/review-scraper` can feed into the 15-signal scoring system
- Review `@openclaw/web-scraper` as a foundation for custom scrapers

### Presentation Skills

| Skill | Creator | Downloads | Description |
|-------|---------|-----------|-------------|
| `@community/slide-generator` | community | 3K+ | Generate presentations from text |
| `@community/pptx-builder` | community | 2K+ | Python-PPTX based slide creation |
| `@community/marp-presenter` | community | 1.5K+ | Markdown to presentation |

**Action Items**:
- Evaluate `@community/pptx-builder` -- may save building from scratch
- If insufficient, build custom skill using Python-PPTX (see priority-skills/presentation-skills.md)

### Data Enrichment Skills

| Skill | Creator | Downloads | Description |
|-------|---------|-----------|-------------|
| `@community/clay-integration` | community | 2K+ | Clay.com API integration |
| `@community/apollo-enrichment` | community | 4K+ | Apollo.io contact enrichment |
| `@community/clearbit-enrichment` | community | 6K+ | Clearbit company/person enrichment |
| `@community/builtwith-checker` | community | 3K+ | Technology stack detection |

**Action Items**:
- Check `@community/clay-integration` compatibility with your existing clay-enrichment skill
- `@community/builtwith-checker` is directly useful for the 15-signal scoring system
- Compose these into a waterfall enrichment pipeline skill

### Social Media Skills

| Skill | Creator | Downloads | Description |
|-------|---------|-----------|-------------|
| `@community/linkedin-poster` | community | 2K+ | Post to LinkedIn company pages |
| `@community/social-scheduler` | community | 5K+ | Schedule posts across platforms |
| `@community/facebook-ads-manager` | community | 3K+ | Facebook/Meta ads management |

**Action Items**:
- Evaluate `@community/linkedin-poster` for company page posting
- Check legal compliance of any LinkedIn automation skills
- `@community/facebook-ads-manager` could be useful for client ad management

---

## Evaluating Skills Before Installation

### Quality Signals to Check

Before installing any ClawHub skill, evaluate these signals:

1. **Stars/Rating**: Community rating (1-5 stars). Look for 4+ stars.
2. **Downloads**: Total installs. Higher = more battle-tested.
3. **Last Updated**: Check the date. Skills not updated in 6+ months may have compatibility issues.
4. **Open Issues**: Check the skill's GitHub repo for unresolved bugs.
5. **Security Review Status**: Has the skill been reviewed by the OpenClaw security team?
6. **Permissions Requested**: Review what the skill asks for. Excessive permissions = red flag.
7. **Dependencies**: How many other skills/packages does it depend on? Fewer = simpler.
8. **Test Coverage**: Does the skill have tests? What is the coverage percentage?
9. **Author Reputation**: Is the author a known community member? Verified publisher?
10. **License**: Is it compatible with your use case (MIT, Apache 2.0, etc.)?

### Evaluation Commands

```bash
# Detailed skill information including all quality signals
openclaw skill info @creator/skill-name --detailed

# View the skill's permissions (what it will have access to)
openclaw skill permissions @creator/skill-name

# View the skill's dependency tree
openclaw skill deps @creator/skill-name

# View recent changes
openclaw skill changelog @creator/skill-name

# Check for known security vulnerabilities
openclaw skill audit @creator/skill-name
```

---

## Forking and Modifying Community Skills

When a ClawHub skill is close to what you need but requires modifications:

### Fork Workflow

```bash
# 1. Clone the skill source to your local skills directory
openclaw skill fork @community/clay-integration

# This creates a local copy at .openclaw/skills/clay-integration/
# with the original skill's code and manifest

# 2. Modify the skill
# Edit files in .openclaw/skills/clay-integration/

# 3. Update the manifest
# Change the name to your namespace: @yourname/clay-integration-custom
# Update version to 1.0.0

# 4. Test your modifications
openclaw skill test clay-integration-custom

# 5. The local skill automatically overrides the original
# Your fork takes priority over any installed version
```

### When to Fork vs Build from Scratch

| Fork When... | Build from Scratch When... |
|--------------|---------------------------|
| Skill does 80%+ of what you need | Skill architecture is wrong for your use case |
| You need to add a feature | No existing skill is close enough |
| You need to fix a bug | Your requirements are highly specialized |
| You want to adapt for a different API | The existing skill is poorly written |

---

## Contributing Your Own Skills to ClawHub

### Publishing Workflow

```bash
# 1. Create your ClawHub account (one-time)
openclaw auth login  # or register at clawhub.openclaw.sh

# 2. Ensure your skill meets quality requirements
openclaw skill validate ./my-skill
# Checks: manifest completeness, test coverage, security scan, documentation

# 3. Package the skill
openclaw skill pack ./my-skill
# Creates: my-skill-1.0.0.tgz

# 4. Publish to ClawHub
openclaw skill publish ./my-skill
# Uploads to ClawHub under your namespace: @yourname/my-skill

# 5. (Optional) Request verification
openclaw skill request-verification @yourname/my-skill
# Submits for OpenClaw team review
```

### Publishing Requirements

- Valid `skill.json` manifest with all required fields
- README.md with usage instructions
- LICENSE file
- At least one test
- No hardcoded credentials or secrets
- Passes `openclaw skill validate` without errors

### Updating Published Skills

```bash
# Bump version in skill.json, then:
openclaw skill publish ./my-skill

# ClawHub will reject if version already exists
# Use semantic versioning: bump patch for fixes, minor for features, major for breaking changes
```

---

## Quality Tiers

ClawHub skills are categorized into three quality tiers:

### Verified (Gold Badge)

- **Reviewed by**: OpenClaw security and quality team
- **Requirements**: Full security audit, comprehensive tests, active maintenance
- **Trust level**: Safe for production use, minimal risk
- **Examples**: Official OpenClaw skills (`@openclaw/*`), partner skills
- **Identifier**: Gold checkmark badge on ClawHub

### Community (Silver Badge)

- **Reviewed by**: Automated checks only (manifest validation, basic security scan)
- **Requirements**: Valid manifest, passes automated checks, has tests
- **Trust level**: Generally safe, but review permissions before installing
- **Examples**: Most community skills (`@community/*`, `@username/*`)
- **Identifier**: Silver community badge on ClawHub

### Experimental (No Badge)

- **Reviewed by**: No review
- **Requirements**: Valid manifest only
- **Trust level**: Use at your own risk, always review code before installing
- **Examples**: New skills, work-in-progress, proof-of-concepts
- **Identifier**: No badge, "Experimental" warning on install

### Trust Recommendations for Your Use Case

For production use (Rise Local, client work):
- **Prefer Verified skills** when available
- **Community skills**: Review code and permissions before using with client data
- **Experimental skills**: Only for testing and prototyping, never with client data

---

## ClawHub Search Strategies for Your Needs

### Finding GHL-Compatible Skills

```bash
openclaw skill search "GoHighLevel"
openclaw skill search "GHL"
openclaw skill search "HighLevel CRM"
openclaw skill search --category crm "pipeline management"
openclaw skill search --category crm "contact management"
```

### Finding Lead Generation Skills

```bash
openclaw skill search "lead enrichment"
openclaw skill search "business discovery"
openclaw skill search "Google Places"
openclaw skill search "Apollo"
openclaw skill search "Clay enrichment"
openclaw skill search --category data "waterfall enrichment"
```

### Finding Marketing Automation Skills

```bash
openclaw skill search --category marketing "local SEO"
openclaw skill search --category marketing "review management"
openclaw skill search --category marketing "content generation"
openclaw skill search --category communication "cold outreach"
```

---

## Research Gaps

- **Exact ClawHub URL**: Confirm clawhub.openclaw.sh is the correct URL
- **Skill counts per category**: The 3,000+ total and per-category estimates need verification
- **Specific skill names**: The skill names listed above are illustrative; actual ClawHub skill names need to be discovered by browsing the actual marketplace
- **GHL-specific skills**: Need to search ClawHub for any existing GoHighLevel integrations
- **Pricing**: Are all ClawHub skills free, or are there paid/premium skills?
- **API rate limits**: Does ClawHub have rate limits on skill downloads or API calls?
- **Private skills**: Can you publish private skills visible only to your team?

---

*Last updated: 2026-02-05*
*Status: Reference guide for ClawHub ecosystem with actionable search strategies and skill recommendations*

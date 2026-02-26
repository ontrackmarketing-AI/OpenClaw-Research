# Press Release Pipeline: Template System, AI Workflow & Distribution

## Overview

The press release pipeline enables SW Recovery Services to produce and distribute 20+ press releases per month as part of a content factory strategy. Each press release serves dual purposes: (1) newswire distribution for SEO backlinks and brand awareness, and (2) repurposing into blog posts, social content, and email campaigns.

The pipeline includes AI-assisted generation from voice memos or brief notes, editorial review, template-based formatting, and automated distribution via newswire services. This document covers the end-to-end workflow from ideation to publication.

**Scale target**: 20 press releases per month across client accounts, with each release repurposed into 2-3 additional content pieces (blog post, social thread, email newsletter snippet).

---

## API / Integration Details

### Newswire Distribution Services

#### PR Newswire (Cision)

**Overview**: Largest press release distribution network with broadest media reach. Best for maximum exposure and SEO impact.

**Pricing (2026)**:
| Distribution Level | Base Cost (400 words) | Additional 100 words | Notes |
|-------------------|----------------------|---------------------|-------|
| Local/Metro | $350 | $85 | Single city/metro |
| State | $500-$700 | $85 | Single state |
| Regional | $600-$900 | $85 | Multi-state region |
| National | $805-$1,070 | $340 | US-wide distribution |

**Additional costs**:
- Annual membership: $195-$249 (required)
- Multimedia (images): $200-$400 per image
- AP syndication: Additional fee
- Logo inclusion: $75-$150
- Full national with all extras: Can reach $3,000+ per release

**API/Automation**:
- PR Newswire does not offer a self-service API for automated distribution
- Submissions via web portal or dedicated account representative
- Bulk scheduling available with enterprise accounts
- XML feed integration for content syndication

**Distribution reach**:
- 100+ industry categories for targeting
- 4,500+ websites and newsrooms
- Major search engines (Google News, Yahoo Finance, etc.)
- Social media amplification options

#### Business Wire (Berkshire Hathaway)

**Overview**: Premium distribution with strongest financial/investor relations focus. Better industry targeting granularity than PR Newswire.

**Pricing (2026)**:
| Distribution Level | Base Cost (400 words) | Additional 100 words | Notes |
|-------------------|----------------------|---------------------|-------|
| Local | $475+ | Varies | True cost often $1,050+ |
| Regional | $700-$1,000 | Varies | Multi-state |
| National | $1,000-$1,500 | Varies | ~25% less than PR Newswire |
| International | $2,000+ | Varies | Global distribution |

**Advantages over PR Newswire**:
- 200+ industry categories (vs 100+ for PR Newswire)
- More granular targeting options
- Longer releases supported at lower cost
- Logo included in base pricing

**API/Automation**:
- Business Wire Connect portal for submissions
- No public self-service API
- Enterprise accounts get dedicated submission workflows

#### Budget-Friendly Alternatives

| Service | Cost per Release | Coverage | Best For |
|---------|-----------------|----------|---------|
| EIN Presswire | $99-$399 | US + Global | Budget-conscious |
| Newswire | $99-$499 | US | SMB volume distribution |
| PRWeb (Cision) | $99-$389 | US | SEO-focused |
| GlobeNewswire | $500-$1,500 | Global | Financial/IR |
| OpenPR | Free-$99 | Global | Startup/testing |

**Recommendation for 20/month volume**: Use a mix of EIN Presswire ($149-$199/release) for routine releases and PR Newswire ($350-$805/release) for major announcements. At 20 releases/month:
- Budget approach (EIN Presswire): 20 x $149 = ~$2,980/month
- Mixed approach: 16 routine ($149) + 4 premium ($500) = ~$4,384/month
- Premium approach (PR Newswire): 20 x $500 = ~$10,000/month

### AI Content Generation Tools

| Tool | Capability | Pricing | Best For |
|------|-----------|---------|---------|
| Claude/GPT-4 | Full PR generation from prompts | $20-$100/month | Drafting from notes |
| Copy.ai | Workflow-based PR generation | $49-$249/month | Template automation |
| Writer.com | Enterprise PR agent | $18-$100/user/month | Brand voice consistency |
| Narrato | AI PR generator + workspace | $36-$76/month | Team collaboration |
| Jasper | Template-based content | $49-$125/month | Marketing teams |

### Voice Memo to Content Pipeline

**Architecture**:
```
Steven records voice memo (phone/app)
  --> Transcription (Whisper API / Otter.ai / Rev)
  --> AI processing (Claude/GPT-4)
  --> Draft press release generated
  --> Editorial review in workspace
  --> Approved --> Formatted with template
  --> Distributed via newswire
  --> Auto-repurposed to blog post + social content
```

**Transcription options**:
| Service | Cost | Accuracy | Speed |
|---------|------|----------|-------|
| OpenAI Whisper API | $0.006/minute | 95-98% | Real-time |
| Otter.ai | $10-$25/month | 90-95% | Real-time |
| Rev (human) | $1.50/minute | 99%+ | 12-24 hours |
| Deepgram | $0.0043/minute | 95-97% | Real-time |

---

## Template System

### Press Release Template Structure

```markdown
# [HEADLINE: Clear, newsworthy, includes company name]
## [SUBHEADLINE: Supporting detail or key statistic]

**[CITY, STATE] -- [DATE]** -- [COMPANY NAME], a [brief descriptor],
today announced [key announcement]. [Impact statement that explains
why this matters to the reader.]

### [First Section Header: Key Details]
[2-3 paragraphs covering the main announcement, including specific
details, data points, and context.]

### [Second Section Header: Supporting Information]
[1-2 paragraphs with quotes from leadership, customer testimonials,
or industry context.]

> "[Quote from Steven or company spokesperson about the announcement
> and its significance.]"
> -- **Steven [Last Name]**, [Title], SW Recovery Services

### [Third Section Header: Industry Context or Future Plans]
[1-2 paragraphs positioning the announcement within broader industry
trends or company roadmap.]

### About [COMPANY NAME]
[Boilerplate paragraph: 3-4 sentences describing the company, its
mission, key achievements, and services.]

**Media Contact:**
[Name]
[Title]
[Email]
[Phone]
```

### Template Categories

| Category | Monthly Volume | Typical Topics |
|----------|---------------|---------------|
| Client Success Stories | 6-8 | Recovery milestones, case studies |
| Industry Insights | 4-6 | Market trends, regulatory updates |
| Company Milestones | 2-3 | Hires, partnerships, awards |
| Service Announcements | 2-3 | New offerings, expansions |
| Thought Leadership | 2-3 | Expert commentary, predictions |

### AI Prompt Templates

**Voice memo to PR prompt**:
```
You are a PR writer for SW Recovery Services. Convert the following
voice memo transcript into a professional press release.

TRANSCRIPT:
{transcription}

GUIDELINES:
- Use AP style formatting
- Include a compelling headline and subheadline
- Lead with the most newsworthy element
- Include a quote attributed to Steven
- Keep to 400-600 words (optimal for distribution cost)
- Include the standard boilerplate at the bottom
- Make it factual, not promotional
- Include relevant statistics or data points
```

**Blog post repurposing prompt**:
```
Convert the following press release into a 800-1200 word blog post.

PRESS RELEASE:
{press_release_text}

GUIDELINES:
- Use a more conversational tone
- Expand on the key points with additional context
- Add relevant internal links to services pages
- Include a call-to-action at the end
- Optimize for SEO with target keyword: {keyword}
- Add 2-3 subheadings using H2/H3 tags
```

---

## Implementation Approach

### Phase 1: Infrastructure Setup (Week 1-2)

1. **Select and configure tools**
   - Choose AI generation tool (Claude API or Copy.ai)
   - Set up voice memo transcription (Whisper API via n8n/Make)
   - Configure editorial workspace (Notion, Google Docs, or ClickUp)
   - Create distribution accounts (EIN Presswire + PR Newswire)

2. **Build template library**
   - Create 5 PR templates by category
   - Write company boilerplate paragraph
   - Establish style guide (AP style, tone, terminology)
   - Create AI prompt library for each template category

3. **Set up voice memo pipeline**
   ```
   Mobile App (voice memo) --> Cloud storage (Google Drive/Dropbox)
     --> Webhook trigger (n8n/Make)
     --> Whisper API transcription
     --> Claude API draft generation
     --> Editorial workspace (Notion)
     --> Slack notification to editor
   ```

### Phase 2: Workflow Automation (Week 3-4)

4. **Build n8n / Make.com automation**
   - Voice memo detection trigger
   - Automatic transcription
   - AI draft generation with template selection
   - Draft delivery to editorial workspace
   - Slack notification to editorial team

5. **Editorial workflow setup**
   - Draft --> Editor Review --> Revisions --> Final Approval --> Distribution
   - Kanban board in Notion/ClickUp for status tracking
   - Approval checklist (facts verified, quotes approved, legal reviewed)
   - Version history and audit trail

6. **Distribution automation**
   - Scheduled distribution via newswire portal
   - Auto-post to company blog (WordPress REST API)
   - Auto-share to social channels (Buffer/Hootsuite)
   - Auto-generate email newsletter snippet

### Phase 3: Repurposing Pipeline (Week 4-5)

7. **Content repurposing workflow**
   ```
   Approved Press Release
     |
     ├── Blog Post (AI-expanded, 800-1200 words)
     │   └── Publish to WordPress
     |
     ├── LinkedIn Post (300-word summary)
     │   └── Schedule via Buffer
     |
     ├── Twitter/X Thread (5-7 tweets)
     │   └── Schedule via Buffer
     |
     ├── Email Newsletter Snippet (100-word summary)
     │   └── Add to weekly digest template
     |
     └── Social Media Graphics (Canva template)
         └── Auto-generate with key stats/quotes
   ```

### Phase 4: Scale Operations (Month 2+)

8. **Ramp to 20/month production**
   - See `scale-operations.md` for detailed scaling plan
   - Week 1-2: 5 releases/week target
   - Week 3-4: Optimize for speed and quality balance
   - Month 2: Full 20/month cadence

---

## Cost Implications

### Monthly Operating Costs (20 releases/month)

| Item | Cost | Notes |
|------|------|-------|
| AI generation (Claude API) | $50-$100/month | ~20 drafts + repurposing |
| Transcription (Whisper API) | $10-$20/month | Voice memo processing |
| Newswire distribution | $2,980-$10,000/month | Depends on service tier |
| Editorial workspace (Notion/ClickUp) | $10-$25/month | Team plan |
| Automation (n8n/Make) | $20-$50/month | Workflow processing |
| Social scheduling (Buffer) | $15-$100/month | Multi-channel posting |
| **Total** | **$3,085-$10,295/month** | Mostly distribution cost |

### Cost Per Press Release

| Approach | Distribution | AI/Tools | Total Per Release |
|----------|-------------|---------|-------------------|
| Budget (EIN) | $149 | $5 | ~$154 |
| Mixed | $200-$300 avg | $5 | ~$205-$305 |
| Premium (PR Newswire) | $500-$1,000 | $5 | ~$505-$1,005 |

### One-Time Setup Costs

| Item | Cost | Notes |
|------|------|-------|
| Template development | Included in build hours | 5 templates |
| AI prompt engineering | Included in build hours | Prompt library |
| Automation workflow building | Included in build hours | n8n/Make flows |
| Brand asset preparation | $0-$500 | Logos, images for PRs |

---

## Estimated Build Hours

| Task | Hours | Notes |
|------|-------|-------|
| Tool selection and account setup | 3-4 | AI, transcription, newswire |
| Template library creation (5 templates) | 6-8 | PR templates, style guide |
| AI prompt engineering (per category) | 4-6 | Prompt tuning, testing |
| Voice memo pipeline automation | 6-8 | n8n/Make workflow, Whisper |
| Editorial workspace configuration | 3-4 | Notion/ClickUp boards, checklists |
| Distribution workflow setup | 3-4 | Newswire accounts, scheduling |
| Content repurposing automation | 6-8 | Blog, social, email flows |
| WordPress integration | 3-4 | REST API auto-publish |
| Testing and QA (full pipeline) | 4-6 | End-to-end validation |
| Training for editorial team | 3-4 | Workflow documentation, walkthrough |
| **Total** | **41-56 hours** | |

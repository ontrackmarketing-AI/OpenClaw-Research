# Scale Operations: 20 Press Releases/Month Production Workflow

## Overview

This document details the operational plan for producing 20 press releases per month for SW Recovery Services and its client portfolio. At this volume, the process must be systematized with clear roles, editorial calendars, quality controls, and approval workflows to maintain consistency while avoiding bottlenecks.

20 releases per month translates to approximately 5 per week, or 1 per business day. Each release generates 2-3 additional content pieces (blog post, social content, email snippet), meaning the total content factory output is 60-80 pieces per month.

**Key challenge**: Balancing AI-generated speed with human editorial quality at scale. The solution is a hybrid model where AI handles first drafts and repurposing, while humans handle ideation, fact-checking, quote approval, and final review.

---

## API / Integration Details

### Content Management Stack

| Component | Tool | Purpose | Monthly Cost |
|-----------|------|---------|-------------|
| Editorial calendar | Notion or ClickUp | Planning, assignments, tracking | $10-$25 |
| AI drafting | Claude API | First draft generation | $50-$100 |
| Transcription | Whisper API | Voice memo processing | $10-$20 |
| Automation | n8n or Make.com | Workflow orchestration | $20-$50 |
| Asset management | Google Drive | File storage, sharing | $0-$12 |
| Distribution | EIN Presswire + PR Newswire | Newswire distribution | $3,000-$10,000 |
| Blog publishing | WordPress REST API | Auto-publish blog versions | Included |
| Social scheduling | Buffer or Hootsuite | Multi-channel posting | $15-$100 |
| Communication | Slack | Team coordination, approvals | $0-$8.75/user |

### Automation Workflows

**Workflow 1: Voice Memo to Draft**
```
Voice memo uploaded to Google Drive folder
  --> n8n detects new file
  --> Whisper API transcribes audio
  --> Claude API generates PR draft (using category template)
  --> Draft added to Notion editorial board (status: "Draft Ready")
  --> Slack notification to assigned editor
```

**Workflow 2: Approved to Published**
```
PR status changed to "Approved" in Notion
  --> n8n detects status change
  --> Format PR for newswire submission (clean text)
  --> Queue for distribution (scheduled date/time)
  --> Generate blog post version via Claude API
  --> Generate social media snippets
  --> Schedule social posts via Buffer API
  --> Publish blog post via WordPress REST API
  --> Add email snippet to weekly digest template
  --> Slack notification: "PR published and distributed"
```

**Workflow 3: Performance Tracking**
```
Distribution confirmation received
  --> Log distribution details (date, service, cost)
  --> Monitor Google News indexing (24-48 hours)
  --> Check backlink generation (7-14 days)
  --> Aggregate metrics to monthly report
```

---

## Production Workflow

### Weekly Schedule (5 Releases/Week)

| Day | Activity | Details |
|-----|----------|---------|
| **Monday** | Planning + 1 Release | Weekly planning meeting (30 min), distribute 1 PR |
| **Tuesday** | 1 Release + Drafting | Distribute 1 PR, AI-generate 2-3 new drafts |
| **Wednesday** | 1 Release + Review | Distribute 1 PR, editorial review of upcoming |
| **Thursday** | 1 Release + Approvals | Distribute 1 PR, Steven/client approvals |
| **Friday** | 1 Release + Reporting | Distribute 1 PR, weekly performance review |

### Monthly Content Calendar

**Week 1 (Releases 1-5)**
| # | Category | Topic Source | Distribution |
|---|----------|-------------|-------------|
| 1 | Client Success | Voice memo from Steven | PR Newswire (premium) |
| 2 | Industry Insight | Market research/trends | EIN Presswire |
| 3 | Service Announcement | Product update/new offering | EIN Presswire |
| 4 | Thought Leadership | Expert commentary | EIN Presswire |
| 5 | Client Success | Case study/milestone | EIN Presswire |

**Week 2 (Releases 6-10)**
| # | Category | Topic Source | Distribution |
|---|----------|-------------|-------------|
| 6 | Company Milestone | Hire/partnership/award | PR Newswire (premium) |
| 7 | Industry Insight | Regulatory update | EIN Presswire |
| 8 | Client Success | Recovery outcome | EIN Presswire |
| 9 | Thought Leadership | Industry prediction | EIN Presswire |
| 10 | Service Announcement | Feature/capability | EIN Presswire |

**Week 3 (Releases 11-15)**
| # | Category | Topic Source | Distribution |
|---|----------|-------------|-------------|
| 11 | Client Success | Voice memo from Steven | PR Newswire (premium) |
| 12 | Industry Insight | Data/research findings | EIN Presswire |
| 13 | Company Milestone | Growth/expansion | EIN Presswire |
| 14 | Client Success | Testimonial-based | EIN Presswire |
| 15 | Thought Leadership | Trend analysis | EIN Presswire |

**Week 4 (Releases 16-20)**
| # | Category | Topic Source | Distribution |
|---|----------|-------------|-------------|
| 16 | Service Announcement | New process/tool | PR Newswire (premium) |
| 17 | Industry Insight | Market commentary | EIN Presswire |
| 18 | Client Success | Recovery milestone | EIN Presswire |
| 19 | Company Milestone | Team/culture update | EIN Presswire |
| 20 | Thought Leadership | Monthly roundup/outlook | EIN Presswire |

### Distribution Strategy

- **4 premium releases/month** (PR Newswire): Major announcements, significant client wins, company milestones
- **16 standard releases/month** (EIN Presswire): Routine content, thought leadership, industry commentary
- **Monthly cost**: 4 x $500 + 16 x $149 = $4,384/month for distribution

---

## Editorial Workflow

### Role Assignments

| Role | Responsibility | Time/Week | Who |
|------|---------------|-----------|-----|
| Content Strategist | Calendar planning, topic selection, assignment | 3-4 hours | OpenClaw team |
| AI Draft Manager | Prompt engineering, AI draft generation, template management | 5-6 hours | OpenClaw team |
| Editor | Review, fact-check, refine AI drafts, ensure brand voice | 8-10 hours | Dedicated editor |
| Approver | Final review, quote approval | 2-3 hours | Steven (or delegate) |
| Distribution Manager | Newswire submission, scheduling, monitoring | 3-4 hours | OpenClaw team |
| Repurposing Specialist | Blog, social, email conversion | 5-6 hours | OpenClaw team |

**Total team hours**: ~26-33 hours/week for 20 releases + repurposed content

### Approval Process

```
Stage 1: AI Draft Generated
  |
  v
Stage 2: Editor Review (24-48 hour turnaround)
  - Fact-checking
  - Brand voice alignment
  - AP style compliance
  - SEO optimization
  - Word count target (400-600 words)
  |
  v
Stage 3: Revision (if needed, 24 hour turnaround)
  - Address editor comments
  - Refine messaging
  |
  v
Stage 4: Approval (24 hour turnaround)
  - Steven or delegate reviews
  - Quote approval
  - Legal/compliance check (if sensitive)
  - Approve or request changes
  |
  v
Stage 5: Distribution Queue
  - Scheduled for target date
  - Formatted for newswire
  - Multimedia attached (images, logos)
  |
  v
Stage 6: Published
  - Distributed via newswire
  - Blog version published
  - Social content scheduled
  - Email snippet added to digest
```

### Quality Control Checklist

**Pre-Publication Checklist**:
- [ ] Headline is clear, newsworthy, includes company name
- [ ] Lead paragraph answers who/what/when/where/why
- [ ] All facts and statistics are verified
- [ ] Quotes are approved by attributed spokesperson
- [ ] Company boilerplate is current and accurate
- [ ] Media contact information is correct
- [ ] Word count is within 400-600 target range
- [ ] AP style formatting is consistent
- [ ] No promotional language (reads as news, not advertising)
- [ ] SEO keywords incorporated naturally
- [ ] Distribution category and targeting are appropriate
- [ ] Multimedia assets meet specifications

**Monthly Quality Audit**:
- Review 5 random releases for quality consistency
- Track editor revision rate (target: <30% need major revisions)
- Monitor AI draft acceptance rate (target: >70% usable with minor edits)
- Check distribution reach and pickup rates
- Verify all backlinks are live and indexed

---

## Content Ideation System

### Topic Pipeline

Maintain a rolling 60-day topic pipeline with at least 40 topics queued at any time (2x the monthly output):

**Topic sources**:
1. **Steven voice memos** (8-10/month): Real-time insights, client updates, market observations
2. **Industry monitoring** (4-6/month): News alerts, regulatory changes, market trends
3. **Client milestones** (4-6/month): Recovery outcomes, case completions, anniversaries
4. **Planned events** (2-4/month): Conferences, partnerships, product launches
5. **Seasonal/cyclical** (2-4/month): Year-end reviews, quarterly outlooks, industry events

### Ideation Meeting (Weekly, 30 minutes)

**Agenda**:
1. Review this week's distribution performance (5 min)
2. Confirm next week's 5 releases (10 min)
3. Add new topics to pipeline (10 min)
4. Address any bottlenecks or issues (5 min)

---

## Scaling Ramp Plan

### Month 1: Ramp to 10/Month

| Week | Target | Focus |
|------|--------|-------|
| Week 1 | 2 releases | Pipeline setup, first distributions |
| Week 2 | 2 releases | Refine workflow, optimize templates |
| Week 3 | 3 releases | Add voice memo pipeline |
| Week 4 | 3 releases | Full workflow with repurposing |

### Month 2: Ramp to 15/Month

| Week | Target | Focus |
|------|--------|-------|
| Week 5 | 3 releases | Consistent cadence established |
| Week 6 | 4 releases | Increase daily output |
| Week 7 | 4 releases | Optimize editorial turnaround |
| Week 8 | 4 releases | Smooth operations at 4/week |

### Month 3: Full Speed 20/Month

| Week | Target | Focus |
|------|--------|-------|
| Week 9 | 5 releases | Full capacity target |
| Week 10 | 5 releases | Fine-tune all processes |
| Week 11 | 5 releases | Optimize automation touchpoints |
| Week 12 | 5 releases | Steady state operations |

---

## Performance Metrics

### KPIs to Track Monthly

| Metric | Target | Measurement |
|--------|--------|-------------|
| Releases published | 20/month | Count |
| On-time publication rate | >90% | Scheduled vs actual |
| Editor revision rate | <30% major | Revisions needed |
| AI draft acceptance rate | >70% usable | Minor edits only |
| Google News pickup | >50% indexed | Google News search |
| Backlinks generated | 5-15 per release | Ahrefs/SEMrush |
| Blog traffic from PR content | +20% MoM | Google Analytics |
| Social engagement on PR content | Baseline +15% | Buffer analytics |
| Cost per release (all-in) | <$300 avg | Total costs / 20 |
| Time from ideation to publish | <5 business days | Workflow tracking |

---

## Cost Implications

### Monthly Operating Costs at Scale (20/month)

| Item | Cost | Notes |
|------|------|-------|
| Newswire distribution | $4,384/month | 4 premium + 16 standard |
| AI tools (Claude API) | $50-$100/month | Drafting + repurposing |
| Transcription (Whisper) | $10-$20/month | Voice memos |
| Editorial workspace | $10-$25/month | Notion/ClickUp |
| Automation (n8n/Make) | $20-$50/month | Workflows |
| Social scheduling | $15-$100/month | Buffer/Hootsuite |
| **Tools total** | **$4,489-$4,679/month** | |
| Editorial labor (part-time editor) | $2,000-$3,500/month | 10-15 hrs/week |
| Content strategist (part-time) | $1,500-$2,500/month | 5-8 hrs/week |
| **Labor total** | **$3,500-$6,000/month** | |
| **Grand total** | **$7,989-$10,679/month** | All-in operational cost |

### Cost Per Release (Fully Loaded)

| Component | Budget | Standard | Premium |
|-----------|--------|----------|---------|
| Distribution | $149 | $200-$300 | $500-$1,000 |
| AI generation | $3-$5 | $3-$5 | $3-$5 |
| Editorial labor | $100-$175 | $100-$175 | $100-$175 |
| Tools/automation | $10-$15 | $10-$15 | $10-$15 |
| **Total per release** | **$262-$344** | **$313-$495** | **$613-$1,195** |

---

## Estimated Build Hours

| Task | Hours | Notes |
|------|-------|-------|
| Content calendar system setup (Notion/ClickUp) | 4-6 | Boards, templates, automations |
| Editorial workflow design | 3-4 | Stages, checklists, assignments |
| Approval process configuration | 2-3 | Stakeholder routing, notifications |
| AI prompt library refinement | 4-6 | Category-specific prompts |
| Distribution account optimization | 2-3 | Bulk scheduling, targeting profiles |
| Repurposing automation workflows | 6-8 | Blog, social, email pipelines |
| Quality control framework | 3-4 | Checklists, audit process |
| Performance dashboard | 4-6 | KPI tracking, reporting |
| Team training and documentation | 4-6 | SOPs, training materials |
| Ramp period oversight (Month 1-2) | 8-12 | Monitoring, adjustment, optimization |
| **Total** | **40-58 hours** | Over initial 8-week ramp |

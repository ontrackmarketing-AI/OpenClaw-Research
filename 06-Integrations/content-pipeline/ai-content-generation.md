# AI Content Generation Workflow: Voice Memos to Blog Posts & Press Releases

## Overview

Steven records voice memos throughout his day — insights about the industry, recovery tips,
client success stories, and business commentary. These voice recordings are raw gold that
need to be transformed into polished blog posts, press releases, LinkedIn articles, and
social media content while preserving Steven's authentic voice and expertise.

This document outlines the end-to-end content generation pipeline: from voice memo capture
through AI transformation to SEO-optimized published content, with a human-in-the-loop
editorial process to ensure quality and brand alignment.

**Content Pipeline:**
```
Voice Memo (Plaud NotePin / Phone recording)
    |
    v
Transcription (Plaud API / Whisper)
    |
    v
AI Content Generation (Claude/GPT)
    - Blog post draft
    - Press release draft
    - LinkedIn post
    - Social media snippets
    |
    v
Editorial Review (Steven / VA)
    - Fact-check claims
    - Tone alignment
    - Brand consistency
    |
    v
SEO Optimization
    - Keyword insertion
    - Meta tags
    - Internal linking
    |
    v
Publishing
    - Phase 1: Manual WordPress posting
    - Phase 2: Automated WordPress API publishing
```

**Content Types from Voice Memos:**
| Content Type | Frequency | Word Count | Purpose |
|-------------|-----------|------------|---------|
| Blog Post | 2-4/week | 800-1,500 | SEO, thought leadership |
| Press Release | 1-2/month | 400-600 | PR distribution, backlinks |
| LinkedIn Article | 1-2/week | 500-1,000 | Professional network growth |
| Social Posts | 3-5/week | 50-280 chars | Engagement, traffic driving |
| Newsletter Excerpt | 1/week | 200-400 | Email marketing |

---

## API/Integration Details

### AI Model Selection

| Model | Use Case | Cost (per 1M tokens) | Strengths |
|-------|----------|---------------------|-----------|
| Claude Sonnet 4.5 | Blog post drafts, long-form | $3 input / $15 output | Nuanced tone matching, long context |
| GPT-4o | Quick social posts, summaries | $2.50 input / $10 output | Fast, good at concise content |
| GPT-4o-mini | Bulk generation, first drafts | $0.15 input / $0.60 output | Cost-effective for volume |
| Claude Haiku 4.5 | SEO metadata, social snippets | $0.80 input / $4 output | Fast, affordable |

**Recommendation:** Use Claude Sonnet 4.5 for blog posts and press releases (quality matters),
GPT-4o-mini for social media snippets and bulk variations (cost matters).

### Tone Matching System

The most critical challenge: making AI content sound like Steven, not like a robot.

**Tone Profile Construction:**
1. Collect 20-30 samples of Steven's existing content (emails, social posts, website copy)
2. Collect 5-10 voice memo transcripts
3. Feed samples to Claude with a tone analysis prompt
4. Generate a "Steven Voice Profile" document

**Tone Profile Prompt:**
```
Analyze the following writing samples from Steven, the owner of SW Recovery
Services. Extract and document:

1. VOCABULARY: Words and phrases Steven uses frequently
2. SENTENCE STRUCTURE: Average length, simple vs complex sentences
3. TONE: Formal/informal, empathetic/authoritative, technical/accessible
4. PERSUASION STYLE: How Steven makes arguments and builds trust
5. INDUSTRY JARGON: Specific terms from the recovery/collections industry
6. PERSONAL TOUCHES: Anecdotes, humor style, opening/closing patterns
7. EMOTIONAL RANGE: How Steven expresses confidence, concern, expertise

Output a "Voice Profile" that can be used as a system prompt for future
content generation. Include specific examples for each category.

Writing samples:
{samples}
```

### Content Generation Prompts

#### Blog Post Generation Prompt

```
You are a ghostwriter for Steven, owner of SW Recovery Services. You write
in Steven's voice (see Voice Profile below).

Voice Profile:
{steven_voice_profile}

TASK: Transform the following voice memo transcript into a blog post.

Transcript:
{transcript}

Requirements:
- Title: Compelling, SEO-friendly, under 60 characters
- Length: 800-1,500 words
- Structure: H2/H3 headings, short paragraphs (2-4 sentences each)
- Opening: Hook that draws readers in (question, statistic, or story)
- Body: 3-5 main points with practical advice
- Closing: Call-to-action relevant to SW Recovery Services
- Tone: Match Steven's natural speaking style (see Voice Profile)
- Include 1-2 personal anecdotes or examples from the transcript
- Do NOT use AI-sounding phrases ("In today's fast-paced world...",
  "It's important to note that...", "Let's dive in...")

SEO Keywords to naturally include:
{target_keywords}

Output format:
---
title: [Title]
meta_description: [155 characters max]
slug: [url-slug]
categories: [comma-separated]
tags: [comma-separated]
featured_image_prompt: [DALL-E prompt for featured image]
---

[Blog post content in markdown]
```

#### Press Release Generation Prompt

```
You are a PR writer for SW Recovery Services. Write a press release based
on the following voice memo where Steven discusses a company announcement.

Voice Profile: {steven_voice_profile}
Transcript: {transcript}

Requirements:
- AP Style formatting
- Headline: Factual, newsworthy (under 100 characters)
- Subheadline: One sentence expanding on headline
- Dateline: [City, State] — [Month Day, Year]
- First paragraph: Who, what, when, where, why
- Body: 2-3 paragraphs with quotes from Steven
- Boilerplate: About SW Recovery Services (standard company description)
- Contact information block at end
- Length: 400-600 words
- Tone: Professional but accessible
```

#### Social Media Snippets Prompt

```
Extract 3-5 social media posts from the following blog post. Each post
should work standalone and drive traffic back to the full article.

Blog Post: {blog_post_content}
Article URL: {url}

For each post, create:
1. LinkedIn post (200-300 words, professional tone, 3-5 hashtags)
2. Twitter/X post (under 280 characters, include link)
3. Facebook post (100-200 words, conversational tone)

Match Steven's voice: {steven_voice_profile_summary}
```

### SEO Optimization Pipeline

#### Keyword Research Integration

```python
def get_target_keywords(topic: str) -> list:
    """Get SEO keywords for a blog post topic using Ahrefs or SEMrush API."""
    # Option 1: Use Ahrefs API (if available)
    # Option 2: Use Google Search Console data
    # Option 3: Use AI to suggest keywords based on topic

    prompt = f"""
    Suggest 5-10 SEO keywords for a blog post about: {topic}
    Industry: Debt recovery, collections, financial services
    Target audience: Business owners with unpaid receivables
    Include:
    - 1-2 primary keywords (high volume, medium competition)
    - 3-5 long-tail keywords (lower volume, lower competition)
    - 2-3 related terms for semantic SEO

    Output as JSON array with search intent for each keyword.
    """
    # Call AI model for keyword suggestions
    return ai_suggest_keywords(prompt)
```

#### On-Page SEO Checklist (Automated)

```python
def seo_optimize(blog_post: str, keywords: list) -> dict:
    """Check and optimize blog post for SEO best practices."""
    checks = {
        'title_length': len(blog_post.title) <= 60,
        'meta_description_length': 120 <= len(blog_post.meta) <= 155,
        'primary_keyword_in_title': keywords[0] in blog_post.title.lower(),
        'primary_keyword_in_first_paragraph': keywords[0] in blog_post.paragraphs[0].lower(),
        'h2_headings_count': blog_post.h2_count >= 3,
        'word_count': 800 <= blog_post.word_count <= 2000,
        'internal_links': blog_post.internal_link_count >= 2,
        'external_links': blog_post.external_link_count >= 1,
        'image_alt_text': all(img.alt for img in blog_post.images),
        'readability_score': blog_post.flesch_score >= 60,  # Easy to read
        'keyword_density': 1.0 <= blog_post.keyword_density(keywords[0]) <= 3.0,
    }
    return checks
```

### WordPress Publishing API

#### Phase 1: Manual Publishing (Current)
- AI generates blog post in markdown
- Steven/VA reviews and edits in Google Docs or Notion
- Manual copy-paste into WordPress editor
- Publish with appropriate categories, tags, featured image

#### Phase 2: Automated Publishing

```python
import requests

WORDPRESS_URL = "https://swrecoveryservices.com/wp-json/wp/v2"
WP_USERNAME = "api-user"
WP_APP_PASSWORD = "xxxx xxxx xxxx xxxx"

def publish_to_wordpress(post: dict, status: str = 'draft') -> dict:
    """Publish a blog post to WordPress via REST API."""
    response = requests.post(
        f"{WORDPRESS_URL}/posts",
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        json={
            'title': post['title'],
            'content': post['content_html'],
            'status': status,          # 'draft' or 'publish'
            'slug': post['slug'],
            'categories': post['category_ids'],
            'tags': post['tag_ids'],
            'meta': {
                'description': post['meta_description'],
            },
            'excerpt': post['excerpt'],
        }
    )
    return response.json()
```

**WordPress Application Passwords**: Generate in WordPress admin under Users > Your Profile > Application Passwords. These are separate from login passwords and can be revoked independently.

---

## Implementation Approach

### Phase 1: Manual Pipeline with AI Assistance (Weeks 1-2)

1. **Voice Memo Intake**: Steven records via Plaud NotePin
2. **Transcription**: Plaud auto-transcribes (webhook to n8n)
3. **AI Draft Generation**: n8n triggers Claude API with transcript + tone profile
4. **Delivery**: Draft sent to Steven via email/Notion for review
5. **Manual Publishing**: Steven/VA publishes approved content to WordPress

**n8n Workflow:**
```
[Plaud Webhook: audio_transcribe.completed]
    |
    v
[Code Node: Extract transcript text + topic detection]
    |
    v
[HTTP Request: Claude API - generate blog post draft]
    |
    v
[HTTP Request: Claude API - generate social media snippets]
    |
    v
[HTTP Request: Claude API - SEO keyword suggestions]
    |
    v
[Code Node: Combine into editorial package]
    |
    v
[Email/Notion: Send draft package to Steven for review]
```

### Phase 2: Semi-Automated Pipeline (Weeks 3-4)

1. Add WordPress REST API integration to n8n
2. AI generates draft and creates WordPress draft post automatically
3. Steven reviews in WordPress editor (familiar interface)
4. One-click publish after review
5. Auto-generate and schedule social media posts

### Phase 3: Full Content Factory (Month 2+)

1. Voice memo -> multiple content pieces (blog + LinkedIn + social + newsletter)
2. SEO keyword tracking and performance feedback loop
3. Content calendar management in n8n
4. Automated featured image generation (DALL-E / Midjourney API)
5. Cross-posting to LinkedIn, Medium, and other platforms
6. Analytics feedback: which topics perform best -> inform future content

### Editorial Review Process

```
AI generates draft
    |
    v
[Auto-checks: fact claims, brand mentions, competitor references]
    |
    v
[Draft delivered to reviewer with checklist]
    |
    v
Reviewer checks:
    [ ] Factual accuracy (claims, statistics, legal references)
    [ ] Tone sounds like Steven (not robotic or generic)
    [ ] No AI-sounding phrases or filler
    [ ] CTA is relevant and natural
    [ ] SEO keywords present but not forced
    [ ] No competitor mentions or negative comparisons
    [ ] Contact info and links are correct
    |
    v
[Approve / Request revisions / Reject]
    |
    v
If revisions needed:
    - Specific feedback sent back to AI for revision
    - OR manual edits in WordPress draft
```

### Content Calendar Structure

| Day | Content Type | Source | Status |
|-----|-------------|--------|--------|
| Monday | Blog Post | Voice memo from previous week | AI draft -> review -> publish |
| Tuesday | LinkedIn Article | Repurposed blog content | Auto-generated from Monday's post |
| Wednesday | Social Posts (3x) | Blog excerpts | Auto-scheduled |
| Thursday | Blog Post #2 | Voice memo or CallRail insight | AI draft -> review -> publish |
| Friday | Newsletter | Weekly roundup | Auto-compiled from week's content |

---

## Cost Implications

### AI API Costs (Monthly)

| Content Type | Volume | Tokens/Piece | Model | Monthly Cost |
|-------------|--------|-------------|-------|-------------|
| Blog Posts | 8/month | ~3,000 output | Claude Sonnet 4.5 | ~$0.36 |
| Press Releases | 2/month | ~1,500 output | Claude Sonnet 4.5 | ~$0.05 |
| Social Snippets | 20/month | ~500 output | GPT-4o-mini | ~$0.01 |
| LinkedIn Posts | 8/month | ~800 output | GPT-4o-mini | ~$0.01 |
| SEO Keywords | 10/month | ~500 output | GPT-4o-mini | ~$0.01 |
| **Total AI cost** | | | | **~$0.44/month** |

*AI content generation is extremely cost-effective at this volume.*

### Tool/Platform Costs

| Tool | Cost | Purpose |
|------|------|---------|
| Plaud subscription | $7.99-19.99/mo | Transcription (already covered) |
| Claude API | ~$0.50/mo | Blog post generation |
| OpenAI API | ~$0.05/mo | Social snippets, SEO |
| WordPress hosting | Existing | Publishing platform |
| n8n (self-hosted) | $0 | Pipeline orchestration |
| **Total incremental** | **~$0.55/month** | |

### Human Costs (Most Significant)

| Role | Time/Week | Rate | Monthly Cost |
|------|-----------|------|-------------|
| Steven (review/approve) | 1-2 hours | $0 (owner time) | $0 |
| VA (editing, publishing) | 3-5 hours | $15-25/hr | $180-500/month |

**The human editorial time is the dominant cost, not the AI generation.**

---

## Estimated Build Hours

| Phase | Tasks | Hours |
|-------|-------|-------|
| **Phase 1: Manual Pipeline** | | |
| Tone profile creation | Collect samples, generate voice profile | 4-6 |
| Prompt engineering | Blog, press release, social prompts | 6-8 |
| n8n workflow (Plaud -> AI -> email) | Webhook, API calls, email delivery | 6-8 |
| Testing with real voice memos | Generate, review, iterate on prompts | 4-6 |
| **Phase 2: WordPress Integration** | | |
| WordPress REST API setup | Application passwords, draft creation | 3-4 |
| n8n WordPress publishing nodes | Auto-create drafts, category mapping | 4-6 |
| SEO optimization automation | Keyword check, meta generation | 3-4 |
| **Phase 3: Full Content Factory** | | |
| Multi-format generation | Blog -> LinkedIn -> social -> newsletter | 6-8 |
| Content calendar automation | Scheduling, cross-posting | 4-6 |
| Analytics feedback loop | Track performance, inform future content | 4-6 |
| **Total** | | **44-62 hours** |

### Phase 1 Standalone: 20-28 hours (recommended starting point)

### Dependencies
- [ ] Plaud webhook integration (from plaud-api-webhook.md)
- [ ] Claude API key (Anthropic account)
- [ ] OpenAI API key (for GPT-4o-mini social snippets)
- [ ] 20-30 writing samples from Steven for tone profile
- [ ] WordPress site with REST API enabled
- [ ] n8n instance with HTTP Request and Code nodes

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| AI content sounds generic | Low engagement, brand damage | Invest in tone profile; iterate prompts weekly |
| Google penalizes AI content | SEO rankings drop | Human editing; unique voice; no mass-produced feel |
| Steven bottlenecks review | Content pipeline stalls | Train VA to do first-pass review; batch approvals |
| Factual errors in AI output | Credibility damage | Mandatory fact-check step; claims verification |
| Tone drift over time | Inconsistent brand voice | Re-calibrate tone profile quarterly |

---

## References

- [The "Speak First" Workflow (VoiceScriber)](https://voicescriber.com/speak-first-workflow-voice-notes-to-blog-posts)
- [AI Content Creation Guide 2025 (Eesel)](https://www.eesel.ai/blog/ai-content-creation)
- [How to Build a Content Machine (TJ Digital)](https://tjrobertson.com/how-to-build-a-content-machine/)
- [AI Content SEO Best Practices 2026 (Iconier)](https://www.iconier.com/ai-generated-content-seo-2026-best-practices)
- [WordPress REST API Handbook](https://developer.wordpress.org/rest-api/)
- [Anthropic Claude API Documentation](https://docs.anthropic.com/en/docs/about-claude/models)
- [OpenAI API Documentation](https://platform.openai.com/docs/)

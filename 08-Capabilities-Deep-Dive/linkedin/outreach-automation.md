# LinkedIn Outreach Automation

## Overview

LinkedIn outreach is one of the highest-converting B2B lead generation channels when done correctly. The key word is "correctly" -- spammy, templated outreach gets ignored and risks account bans. OpenClaw's approach is semi-automated: AI handles the research-heavy and writing-heavy parts, while a human handles the actual LinkedIn interactions. This preserves personalization quality, maintains compliance with LinkedIn's Terms of Service (to the extent possible), and keeps the human in the loop for all external communications.

---

## Strategy: Semi-Automated, Human-Supervised

**What OpenClaw automates:**
- Target identification from enriched lead data
- Profile research and analysis
- Personalized message drafting (connection requests, follow-ups, pitches)
- Response tracking and follow-up scheduling
- CRM synchronization
- Performance analytics

**What humans do:**
- Review and approve every message before sending
- Send connection requests and messages via LinkedIn UI
- Respond to replies and have real conversations
- Make judgment calls on tone, timing, and approach
- Handle meetings and sales conversations

This division maximizes efficiency (AI does the 80% that is research and writing) while preserving authenticity (human does the 20% that matters most -- actual interaction).

---

## Outreach Workflow

### Step 1: Target Identification

**Source:** Enriched leads from the lead enrichment pipeline that have LinkedIn profiles.

**Target selection criteria:**
- Lead scored in target range (30-60) -- has a real business with marketing gaps
- LinkedIn profile found for the owner/decision-maker
- Not already connected on LinkedIn
- Not already in an active outreach sequence
- Not opted out or marked "do not contact"
- Located in your service area
- In an industry you serve

**Batch size:** 5-15 new targets per day (well within LinkedIn safety limits).

**Implementation:**
```sql
SELECT l.*, c.linkedin_url
FROM leads l
JOIN contacts c ON l.id = c.lead_id
WHERE l.score BETWEEN 30 AND 60
  AND c.linkedin_url IS NOT NULL
  AND l.linkedin_status = 'not_started'
  AND l.location_state = 'TX'
  AND l.industry IN ('plumber', 'hvac', 'solar', 'dentist', 'lawyer')
ORDER BY l.score DESC
LIMIT 15;
```

---

### Step 2: Profile Research

For each target, OpenClaw performs deep research:

**Data gathered:**
- Recent LinkedIn posts and articles (last 30 days)
- Comments they have made on others' posts
- Company page activity and updates
- Mutual connections (people you both know)
- Shared groups or interests
- Career history and tenure at current company
- Education and certifications
- Endorsements and skills
- Recommendations given and received
- Any recent life events (new job, promotion, work anniversary)

**Research output:**
```json
{
  "target": "John Smith, Owner, Smith's Plumbing LLC",
  "linkedin_url": "https://linkedin.com/in/johnsmith-plumber",
  "recent_activity": [
    "Posted about hiring a new technician (3 days ago)",
    "Shared article about plumbing industry trends (2 weeks ago)",
    "Commented on a post about small business challenges"
  ],
  "mutual_connections": 2,
  "shared_groups": ["Austin Business Owners Network"],
  "tenure": "Owner since 2018 (8 years)",
  "personalization_hooks": [
    "Growing business (hiring post)",
    "Engaged in industry community",
    "Austin-based, local connection possible",
    "Shared group membership"
  ],
  "recommended_approach": "Lead with congratulations on growth/hiring, transition to marketing support for growing businesses"
}
```

**Research method:**
- Clay.com for available LinkedIn data
- Serper search: `"John Smith" "Smith's Plumbing" site:linkedin.com`
- Public LinkedIn profile data (if available without login)
- Cross-reference with other enrichment data

---

### Step 3: Connection Request

**Timing:** Send connection requests Tuesday through Thursday, between 8am-11am or 1pm-4pm in the target's timezone. These are peak LinkedIn engagement windows.

**Message format:** LinkedIn allows a 300-character note with connection requests. Every character matters.

**OpenClaw drafts the connection note based on research:**

**Template approach (DO NOT use these verbatim -- each must be unique):**

**If mutual connection exists:**
```
Hi John, I noticed we're both connected with [Mutual Name].
I run a marketing agency here in Austin and love connecting with
fellow local business owners. Would be great to connect!
```

**If they posted recently:**
```
Hi John, saw your post about hiring a new tech -- congrats on
the growth! I work with [service] businesses in Austin on their
marketing. Always happy to connect with growing local companies.
```

**If shared group:**
```
Hi John, fellow Austin Business Owners Network member here.
I help local [industry] companies grow their online presence.
Would love to connect and share insights.
```

**If no specific hook:**
```
Hi John, I came across Smith's Plumbing while researching
top [city] service companies. Impressive 4.7-star rating with
89 reviews! I'd love to connect.
```

**Key principles for connection notes:**
1. Reference something specific (not generic)
2. Establish relevance (local, same industry, mutual connection)
3. No pitch in the connection request (save that for later)
4. Friendly, professional tone
5. Under 250 characters (leave breathing room)
6. Include your value proposition subtly (what you do, not what you're selling)

**Human review:** OpenClaw presents the draft to the human operator, who reviews, edits if needed, and sends via the LinkedIn UI.

---

### Step 4: Wait for Acceptance (2-7 days)

**After sending the connection request:**
- Track status: pending, accepted, ignored, withdrawn
- If accepted within 7 days: move to Step 5
- If not accepted after 14 days: withdraw request (keeps pending count low)
- Do not send a follow-up connection request if ignored (once is enough)

**Expected acceptance rate:** 25-40% with personalized notes (vs 10-15% with no note or generic note).

---

### Step 5: First Message (Day 1-2 after acceptance)

**Purpose:** Deliver value, not a pitch. Build rapport and demonstrate expertise.

**Approach:** Send something genuinely useful to the recipient.

**Message types:**

**Type A: Share relevant insight**
```
Hi John, great to connect! I was looking at your online presence
and noticed something interesting -- you rank on page 2 for
"plumber in Austin" which means you're close to page 1 but not
quite there yet. A few quick SEO fixes could make a big difference.

Happy to share what I noticed if you're interested, no strings
attached.
```

**Type B: Share relevant content**
```
John, glad we connected! I recently put together a guide on
"5 Marketing Mistakes Home Service Companies Make" based on
working with businesses like yours in Austin. Thought it might
be useful for you.

Would you like me to send it over?
```

**Type C: Ask a genuine question**
```
John, thanks for connecting! I'm curious -- as a growing plumbing
business in Austin, what's been your biggest challenge when it
comes to getting new customers? I work with a lot of local service
businesses and I'm always learning from business owners like you.
```

**Key principles:**
- Lead with value (insight, content, genuine interest)
- No pitch, no mention of your services as a solution
- Ask a question to encourage response
- Keep it concise (3-5 sentences)
- Reference specific details from your research

---

### Step 6: Second Message (Day 3-5 after first message)

**If they responded to the first message:**
- Continue the conversation naturally
- Answer their questions
- Provide more value
- Gently gauge interest in improving their marketing

**If they did not respond to the first message:**
- Send a lighter follow-up

**Follow-up example:**
```
Hey John, hope you had a great week! I was browsing your Google
reviews -- your customers clearly love your work (4.7 stars is
impressive!). I noticed you don't have any review responses
though -- replying to reviews can actually boost your ranking
in Google Maps. Quick win!

Anyway, just wanted to share that tip. Let me know if you ever
want to chat about growing your online presence.
```

**Key principles:**
- Different angle than the first message
- Still providing value (actionable tip)
- Not desperate or pushy
- Light CTA at the end

---

### Step 7: Third Message (Day 7-10, only if engaged)

**Only send the pitch message if:**
- They responded to at least one previous message
- Responses showed interest (not "please stop messaging me")
- The conversation naturally leads to your services

**Pitch message example:**
```
John, I've really enjoyed our conversation! Based on what you've
shared and what I've seen of your online presence, I think there's
a real opportunity to get your business more visibility in Austin.

Specifically, I think we could help with:
1. Getting you to page 1 for your top keywords
2. Building a modern website that converts more visitors to calls
3. Setting up a review management system

Would you be open to a quick 15-minute call this week? I can
show you exactly what I'm seeing and what the opportunity looks
like. No pressure either way.
```

**Key principles:**
- Reference the relationship and past conversation
- Be specific about what you can help with (based on enrichment data)
- Keep the ask small (15-minute call, not a full sales meeting)
- Remove pressure ("no pressure either way")
- Only one CTA (schedule a call)

---

### Step 8: Follow-Up or Move On

**If they agree to a call:**
- Schedule immediately (send a Calendly link or suggest 2-3 specific times)
- Confirm the day before
- Prepare a brief audit/presentation based on your enrichment data
- This enters your normal sales process

**If they say "not right now":**
- Thank them, add to nurture list
- Check back in 60-90 days with a new value touchpoint

**If they don't respond to the third message:**
- Stop messaging (three unanswered messages is the maximum)
- Add to long-term nurture list
- May re-engage in 6+ months if their online presence changes (detected by re-scoring)

**If they say "not interested" or ask to stop:**
- Immediately stop all outreach
- Mark as "opted out" in CRM
- Respond politely: "Totally understand, John. Best of luck with the business!"
- Never contact again via LinkedIn

---

## Personalization Engine

OpenClaw generates unique messages by combining:

**Input data:**
```json
{
  "target_name": "John Smith",
  "business_name": "Smith's Plumbing LLC",
  "city": "Austin",
  "industry": "plumber",
  "google_rating": 4.7,
  "google_reviews": 89,
  "website_issues": ["no SSL", "slow page speed", "no analytics"],
  "seo_ranking": "page 2 for 'plumber austin'",
  "recent_linkedin_activity": "posted about hiring",
  "mutual_connections": ["Sarah Jones"],
  "years_in_business": 8,
  "missing_marketing": ["no Google Ads", "no email marketing", "inactive social media"]
}
```

**AI prompt for message generation:**
```
Write a LinkedIn message to {target_name}, owner of {business_name}
in {city}. This is the {first/second/third} message in our outreach
sequence. The goal of this message is {goal}.

Use these personalization details:
{details}

Requirements:
- Maximum {word_count} words
- Conversational, professional tone
- Reference at least one specific detail about their business
- {goal-specific requirement}
- Do NOT use generic phrases like "I came across your profile"
- Do NOT use emoji
- Sound like a real person, not a sales email
```

**Each message is reviewed by a human before sending.** OpenClaw flags messages for the operator and presents them in a review queue with context.

---

## Tracking and Analytics

### Metrics to Track

| Metric | Definition | Target |
|--------|-----------|--------|
| Connection request sent | Total requests sent | 15-20/day |
| Acceptance rate | Accepted / Sent | >30% |
| First message response rate | Responded / First messages sent | >25% |
| Conversation rate | Had 2+ exchanges / Responded | >50% |
| Meeting booked rate | Meetings / Conversations | >15% |
| Client conversion rate | Clients / Meetings | >25% |
| Overall pipeline conversion | Clients / Connection requests sent | >1% |

### Tracking Implementation

Store all LinkedIn activity in your database/Airtable:

```
LinkedIn Outreach Table:
- Lead ID (linked to Leads table)
- Target Name
- LinkedIn URL
- Outreach Status (not_started, connection_sent, connected, message_1_sent, message_2_sent, message_3_sent, meeting_booked, converted, opted_out, no_response)
- Connection Request Date
- Connection Accepted Date
- Message 1 Sent Date
- Message 1 Response Date
- Message 2 Sent Date
- Message 2 Response Date
- Message 3 Sent Date
- Message 3 Response Date
- Meeting Date
- Notes
- Message Drafts (for record-keeping)
```

### Weekly Report

OpenClaw generates a weekly LinkedIn outreach report:

```
LinkedIn Outreach Report - Week of Feb 3-7, 2026

Activity:
- Connection requests sent: 65
- Connections accepted: 23 (35% acceptance rate)
- First messages sent: 18
- Responses received: 6 (33% response rate)
- Meetings booked: 1

Pipeline:
- Active conversations: 4
- Pending connection requests: 42
- Nurture list: 12
- Opted out: 1

Top Performing Messages:
1. Insight-based message about SEO ranking: 50% response rate
2. Google review tip message: 40% response rate
3. Content share message: 20% response rate

Recommendations:
- Insight-based messages outperform content shares 2:1
- Tuesday morning sends have highest acceptance rate
- Consider increasing daily connection requests to 20 (currently 13 avg)
```

---

## CRM Integration

### Sync LinkedIn Activity to GHL (Go High Level)

Every LinkedIn interaction syncs to the contact's record in GHL:

**Sync points:**
- Connection request sent -> Tag: "linkedin_outreach_started"
- Connection accepted -> Tag: "linkedin_connected"
- First message sent -> Note added with message text
- Response received -> Tag: "linkedin_responded", note added
- Meeting booked -> Tag: "linkedin_meeting", pipeline stage updated
- Opted out -> Tag: "linkedin_opt_out", Do Not Contact flag

**Implementation via n8n workflow:**
1. OpenClaw logs LinkedIn activity to Airtable/Supabase
2. n8n watches for new activity records
3. n8n updates corresponding GHL contact via API
4. Tags and notes added automatically
5. Pipeline stage updated on key milestones

---

## Content Sharing for Authority Building

In addition to direct outreach, OpenClaw manages a content sharing strategy on LinkedIn:

**Content types:**
- Industry tips and insights (2-3 per week)
- Case studies (anonymized client results, 1 per week)
- Industry news commentary (as relevant)
- Behind-the-scenes of your agency work (1 per week)
- Client success celebrations (with permission)

**Content benefits for outreach:**
- Targets see your content in their feed after connecting
- Builds credibility before and after outreach messages
- Gives you content to reference in outreach ("I just wrote about this...")
- Increases profile visibility (LinkedIn's algorithm rewards consistent posting)

**OpenClaw content workflow:**
1. Generate content ideas based on industry trends and target audience pain points
2. Draft posts (text + optional image)
3. Human reviews and approves
4. Publish via LinkedIn Share API (official, zero risk)
5. Track engagement metrics
6. Iterate based on what performs best

---

## Safety Guardrails

Built into the OpenClaw LinkedIn outreach workflow:

1. **Daily limit enforcement:** System blocks new connection requests after 25/day
2. **Weekly limit enforcement:** System blocks after 100/week
3. **Pending request cap:** Alert when pending requests exceed 500
4. **Duplicate prevention:** Never send connection request to someone already in pipeline
5. **Opt-out respect:** Immediately stop all contact when requested
6. **Human approval gate:** No message sent without explicit human approval
7. **Activity logging:** Every action logged with timestamp for audit trail
8. **Rate monitoring:** Dashboard showing daily/weekly activity vs limits
9. **Cool-down alerts:** If any restriction detected, halt all automation
10. **Personalization check:** Flag messages that look too similar to previous messages

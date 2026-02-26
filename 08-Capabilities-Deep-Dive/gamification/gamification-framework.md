# Gamification Framework: Sales Team Competition & Engagement

## Overview

This gamification framework designs a points, badges, and leaderboard system to drive sales team performance at SW Recovery Services. The system integrates with Slack for real-time visibility and uses data from GoHighLevel CRM to automatically track and reward sales activities.

Gamification taps into intrinsic motivation (status, mastery, autonomy) and extrinsic rewards (prizes, recognition) to increase sales activity volume, improve conversion rates, and foster healthy team competition.

**Goals**:
- Increase daily sales activity volume by 20-30%
- Improve lead follow-up speed (target: <5 minutes for hot leads)
- Drive adoption of CRM best practices (data entry, pipeline management)
- Build team culture through healthy competition and recognition

---

## API / Integration Details

### Data Sources

| Source | Data | Method | Refresh |
|--------|------|--------|---------|
| GoHighLevel CRM | Deals created/won, pipeline stages, activities | GHL API + Webhooks | Real-time |
| Phone system (CallRail) | Calls made, duration, outcomes | CallRail API | Daily |
| Email platform | Emails sent, opens, replies | API/webhook | Daily |
| LinkedIn (Expandi) | Connection requests, replies, meetings booked | Expandi webhooks | Daily |
| Voice bot | Inbound calls handled, qualified leads | Bot platform API | Real-time |

### GHL Integration Architecture

```
GHL CRM Events (webhooks)
  |
  ├── Contact created --> +5 points
  ├── Note added --> +2 points
  ├── Call logged --> +10 points
  ├── Email sent --> +3 points
  ├── Appointment set --> +25 points
  ├── Deal created --> +20 points
  ├── Deal moved to next stage --> +15 points
  ├── Deal won --> +100 points (+ % of deal value)
  └── Deal lost --> 0 points (no penalty)
  |
  v
Gamification Engine (custom app or platform)
  |
  ├── Calculate running totals
  ├── Check badge thresholds
  ├── Update leaderboard
  └── Send Slack notifications
```

### Slack Integration

**Slack channels**:
| Channel | Purpose | Notifications |
|---------|---------|--------------|
| #sales-leaderboard | Daily/weekly standings | Auto-posted summaries |
| #sales-wins | Deal closings and milestones | Real-time celebrations |
| #sales-badges | Badge achievements | When earned |
| #sales-competition | Active contest updates | Contest-specific |

**Slack Bot capabilities**:
- `/leaderboard` - Show current standings
- `/mypoints` - Show personal score and badge progress
- `/team` - Show team totals
- `/badges` - List available badges and progress
- `/contest` - Show active contest details

**Slack notification examples**:
```
🏆 Sarah just closed a $75,000 deal! +175 points
   Current rank: #2 (1,450 points this month)

🎖️ Mike earned the "Cold Caller" badge!
   Made 50 outbound calls this week

📊 Weekly Leaderboard Update:
   1. Sarah - 1,450 pts ⬆️ (+320)
   2. James - 1,380 pts ⬆️ (+280)
   3. Mike  - 1,200 pts ⬇️ (+150)
```

### Gamification Platform Options

| Platform | Pricing | Slack Integration | CRM Integration | Best For |
|----------|---------|-------------------|-----------------|---------|
| **SalesCompete** | $250/month | Native (Slack-first) | Zapier | Small teams, Slack-centric |
| **Spinify** | $10/user/month | Yes | Salesforce, HubSpot | AI-driven, mid-market |
| **Pointagram** | Free-$75/month | Native | Zapier | Budget-conscious |
| **LevelEleven** | Custom pricing | Yes | Salesforce | Enterprise |
| **Ambition** | Custom pricing | Yes | Salesforce, HubSpot | Enterprise, TV displays |
| **Custom build** | Dev hours only | Slack API | GHL API | Full customization |

**Recommendation**: Start with **Pointagram** (free tier) or **SalesCompete** ($250/month) for quick Slack-native deployment. Migrate to a custom solution if deeper GHL integration is needed.

---

## Points System Design

### Activity Points

| Activity | Points | Rationale |
|----------|--------|-----------|
| **Lead Management** | | |
| New contact created in CRM | 5 | Data capture incentive |
| Contact notes updated | 2 | CRM hygiene |
| Lead qualification completed | 10 | Process adherence |
| **Communication** | | |
| Outbound call made | 10 | Activity volume driver |
| Call >5 minutes (meaningful conversation) | 15 | Quality over quantity |
| Email sent to prospect | 3 | Touchpoint tracking |
| Email reply received | 8 | Engagement reward |
| LinkedIn message sent (Expandi) | 5 | Multi-channel effort |
| LinkedIn reply received | 10 | Engagement quality |
| **Pipeline Progress** | | |
| Appointment/meeting set | 25 | High-value activity |
| Meeting held (attended) | 30 | Completion counts |
| Proposal/quote sent | 20 | Deal progression |
| Deal created in pipeline | 20 | Opportunity generation |
| Deal advanced to next stage | 15 | Pipeline momentum |
| **Revenue** | | |
| Deal won (<$10K) | 50 | Small win recognition |
| Deal won ($10K-$50K) | 100 | Mid-tier celebration |
| Deal won ($50K-$100K) | 200 | Major win |
| Deal won (>$100K) | 500 | Milestone achievement |
| Bonus: % of deal value | 1 pt per $100 | Proportional reward |
| **Speed Bonuses** | | |
| Follow-up within 5 minutes | 15 bonus | Response time incentive |
| Follow-up within 1 hour | 5 bonus | Good response time |
| Same-day follow-up | 2 bonus | Basic expectation |
| **Special Activities** | | |
| Client referral generated | 50 | Growth incentive |
| Testimonial/case study secured | 40 | Content contribution |
| Training/certification completed | 30 | Professional development |

### Points Decay (Optional)

To prevent coasting on early wins, consider monthly point resets or rolling 30-day windows:
- **Full reset**: Points reset to 0 on the 1st of each month (simplest, most competitive)
- **Rolling window**: Only count points from last 30 days (smoother, less volatile)
- **Accumulated + monthly**: Keep lifetime total for badges, use monthly total for leaderboard

**Recommendation**: Monthly reset for leaderboard competition, lifetime accumulation for badge progression.

---

## Badge System

### Badge Categories

**Activity Badges** (earned by volume)
| Badge | Criteria | Icon |
|-------|----------|------|
| First Call | Make your first outbound call | Phone |
| Dialer | 25 calls in a week | Phone+ |
| Cold Caller | 50 calls in a week | Snowflake+Phone |
| Phone Warrior | 100 calls in a week | Sword+Phone |
| Email Pro | 50 emails sent in a week | Envelope |
| Multi-Channel Master | Use all channels (call, email, LinkedIn, text) in one day | Globe |
| Early Bird | Log first activity before 8 AM | Sun |
| Night Owl | Log activity after 6 PM | Moon |

**Pipeline Badges** (earned by progression)
| Badge | Criteria | Icon |
|-------|----------|------|
| Pipeline Builder | Create 10 deals in a month | Wrench |
| Meeting Machine | Set 20 meetings in a month | Calendar |
| Proposal Pro | Send 15 proposals in a month | Document |
| Stage Mover | Advance 25 deals in a month | Arrow |

**Revenue Badges** (earned by closing)
| Badge | Criteria | Icon |
|-------|----------|------|
| First Close | Win your first deal | Star |
| Deal Maker | Close 5 deals in a month | Stars |
| Six Figure Club | Close a deal >$100K | Diamond |
| Million Dollar Member | $1M lifetime revenue | Crown |
| Streak Master | Close deals 5 days in a row | Fire |

**Team/Culture Badges** (earned by collaboration)
| Badge | Criteria | Icon |
|-------|----------|------|
| Team Player | Assist on 3 colleague deals in a month | Handshake |
| Mentor | Help a new team member close their first deal | Graduation |
| Referral King/Queen | Generate 5 client referrals in a month | Gift |
| CRM Champion | 100% CRM data compliance for 30 days | Trophy |

### Badge Display

- Badges appear next to names on the Slack leaderboard
- Badge history visible in `/mypoints` command
- Physical badge board in office (optional)
- LinkedIn profile badge graphics (optional, for recruiting)

---

## Leaderboard Design

### Individual Leaderboard

```
📊 Monthly Sales Leaderboard - February 2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Rank  Name        Points   Deals   Revenue    Trend
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1.   Sarah M.    2,150    8       $425K      ⬆️ +2
  2.   James K.    1,890    6       $380K      ⬇️ -1
  3.   Mike R.     1,750    7       $290K      ⬆️ +1
  4.   Lisa T.     1,620    5       $310K      ─
  5.   Chris B.    1,480    4       $185K      ⬆️ +3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Team Total:     8,890    30      $1.59M
  Monthly Target: 10,000   40      $2.0M
  Progress:       88.9%    75%     79.5%
```

### Team Leaderboard (if multiple teams)

| Team | Points | Deals Won | Revenue | Target % |
|------|--------|-----------|---------|----------|
| Team Alpha | 4,850 | 18 | $890K | 89% |
| Team Bravo | 4,040 | 12 | $700K | 70% |

### Leaderboard Posting Schedule

| Frequency | Channel | Content |
|-----------|---------|---------|
| Real-time | #sales-wins | Individual deal closings |
| Daily (5 PM) | #sales-leaderboard | Daily standings update |
| Weekly (Friday 4 PM) | #sales-leaderboard | Weekly summary with trends |
| Monthly (1st of month) | #sales-leaderboard | Monthly winner announcement |

---

## Competition Mechanics

### Monthly Contests

**Standard monthly contest**:
- Highest points earner wins "Salesperson of the Month"
- Prize: $200 gift card, parking spot, LinkedIn feature
- Runner-up: $100 gift card
- Recognition in team meeting

**Themed contests** (rotate monthly):
| Month | Contest | Prize | Measurement |
|-------|---------|-------|-------------|
| January | "New Year Blitz" | $500 bonus | Most deals created |
| February | "Speed Demon" | Team dinner | Fastest average follow-up time |
| March | "Pipeline Builder" | Day off | Most pipeline value added |
| April | "Referral Rally" | Weekend trip | Most referrals generated |
| May | "Email Champion" | Tech gadget | Highest email reply rate |
| June | "Halfway Hero" | H1 bonus | Best H1 overall performance |

### Weekly Challenges

Short-burst competitions to maintain engagement between monthly contests:

| Challenge Type | Duration | Example | Points |
|---------------|----------|---------|--------|
| Power Hour | 1 hour | Most calls in next hour | 2x points |
| Daily Sprint | 1 day | First to 10 meaningful calls | 50 bonus |
| Team Challenge | 1 week | Combined team target | Team reward |
| Streak Challenge | Ongoing | Consecutive days with a close | Multiplier |

### Anti-Gaming Rules

To prevent point manipulation:
1. **Quality gates**: Calls must be >30 seconds to count (prevent spam dialing)
2. **Duplicate prevention**: Same contact can only generate points once per day
3. **Manager override**: Managers can flag and remove gaming activity
4. **Revenue verification**: Deal won points only awarded after payment confirmed
5. **Peer review**: Team can flag suspicious activity anonymously

---

## Implementation Approach

### Phase 1: Foundation (Week 1-2)

1. **Define points and badges**
   - Finalize point values with sales leadership
   - Design badge criteria and graphics
   - Get team buy-in on rules and anti-gaming policies

2. **Select platform**
   - Evaluate Pointagram, SalesCompete, or custom solution
   - Set up accounts and Slack integration
   - Configure data sources (GHL webhooks, CallRail API)

3. **Slack setup**
   - Create channels (#sales-leaderboard, #sales-wins, #sales-badges)
   - Install gamification bot or custom Slack app
   - Test notification formatting

### Phase 2: Data Integration (Week 3-4)

4. **Connect data sources**
   - GHL CRM webhooks --> Gamification engine
   - CallRail API --> Call activity tracking
   - Email platform --> Send/reply tracking
   - Expandi webhooks --> LinkedIn activity tracking

5. **Build scoring logic**
   - Map CRM events to point values
   - Configure badge threshold triggers
   - Build leaderboard calculation engine
   - Test with sample data

### Phase 3: Launch (Week 5)

6. **Soft launch**
   - Run 1-week pilot with volunteer team members
   - Gather feedback on point values and badge criteria
   - Adjust scoring based on real activity data
   - Fix any integration issues

7. **Full launch**
   - Announce at team meeting with prizes revealed
   - Provide reference card of points and badges
   - Start first monthly contest
   - Monitor adoption and engagement daily

### Phase 4: Optimization (Month 2+)

8. **Iterate based on data**
   - Analyze which activities increased most
   - Adjust point values to incentivize desired behaviors
   - Add new badges based on team feedback
   - Review anti-gaming effectiveness
   - Monthly satisfaction survey

---

## Cost Implications

### Platform Costs

| Option | Monthly Cost | Includes | Best For |
|--------|-------------|----------|---------|
| Pointagram (Free) | $0 | Basic points + leaderboards | Testing/MVP |
| Pointagram (Pro) | $75/month | Full features, Slack | Small team |
| SalesCompete | $250/month | Slack-native, full gamification | Slack-first teams |
| Spinify | $10/user/month | AI-driven, TV displays | Mid-market |
| Custom build | $0/month (dev hours) | Full customization | GHL-native |

### Prize Budget

| Category | Monthly Cost | Notes |
|----------|-------------|-------|
| Monthly winner prizes | $300-$500 | Gift cards, experiences |
| Weekly challenge rewards | $50-$100 | Small prizes, recognition |
| Quarterly big prizes | $250-$500/quarter | Larger experiences, bonuses |
| Annual awards | $500-$1,000/year | Trip, major bonus |
| **Total prize budget** | **$400-$700/month** | |

### Total Monthly Cost

| Component | Cost |
|-----------|------|
| Gamification platform | $0-$250/month |
| Prize budget | $400-$700/month |
| Slack workspace (if new) | $0-$70/month |
| Integration maintenance | Included in dev hours |
| **Total** | **$400-$1,020/month** |

---

## Estimated Build Hours

| Task | Hours | Notes |
|------|-------|-------|
| Points system design and approval | 3-4 | Collaborate with sales leadership |
| Badge design (criteria + graphics) | 4-6 | Design badges, create graphics |
| Platform setup and configuration | 4-6 | Pointagram/SalesCompete or custom |
| Slack channel and bot setup | 3-4 | Channels, notifications, bot commands |
| GHL webhook integration | 6-8 | Map CRM events to points |
| CallRail/email integration | 4-6 | Activity tracking data sources |
| Leaderboard calculation logic | 4-6 | Scoring engine, ranking |
| Testing with sample data | 3-4 | Validate all triggers and calculations |
| Pilot program (1 week) | 4-6 | Monitor, gather feedback |
| Documentation and team training | 3-4 | Rules, reference cards, walkthrough |
| **Total** | **38-54 hours** | |

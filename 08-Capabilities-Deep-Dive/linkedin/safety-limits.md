# LinkedIn Safety Limits and Account Protection

## Overview

LinkedIn actively monitors for automated behavior and aggressively restricts accounts that exceed normal human usage patterns. This document provides specific numerical limits, warmup schedules, timing patterns, and monitoring practices to keep your LinkedIn account safe while running semi-automated outreach through OpenClaw. These limits are based on community-reported thresholds and are deliberately conservative -- it is far better to leave headroom than to trigger a restriction.

---

## Daily Activity Limits

### Connection Requests

| Account Status | Daily Limit | Notes |
|---------------|-------------|-------|
| New account (<1 month) | 10-15 | LinkedIn scrutinizes new accounts most heavily |
| Young account (1-3 months) | 15-20 | Gradually increasing |
| Established account (3-6 months) | 20-25 | Standard operating limit |
| Mature account (6+ months, 500+ connections) | 25-30 | Upper safe limit |
| Account with Sales Navigator | 25-35 | Sales Nav accounts get slightly more leeway |

**Hard rule: Never exceed 30 connection requests in a single day.** Even mature accounts with Sales Navigator should stay below this.

**Connection request quality factors:**
- Requests with personalized notes have higher acceptance rates, which LinkedIn rewards
- High ignore/decline rates signal spam -- LinkedIn may restrict your account
- Withdrawn requests also count negatively (withdraw sparingly)
- Target acceptance rate should be >25% -- if below this, improve your targeting and personalization

### Messages (to existing connections)

| Account Status | Daily Limit | Notes |
|---------------|-------------|-------|
| New account | 20-30 | Keep very conservative |
| Established account | 50-75 | Standard limit |
| Mature account | 75-100 | Upper safe limit |

**Message quality factors:**
- Identical or near-identical messages trigger spam detection
- Messages reported as spam severely damage your account standing
- Long messages with lots of links look spammy
- Reply rate matters -- messages that get replies signal legitimate conversation

### InMail (Sales Navigator only)

| Plan | Monthly InMail Credits | Daily Recommended Max |
|------|----------------------|----------------------|
| Sales Navigator Core | 50/month | 5-10 |
| Sales Navigator Advanced | 100/month | 10-15 |

**InMail is self-limiting due to credit scarcity.** Use credits strategically for high-value targets only.

### Profile Views

| Account Status | Daily Limit | Notes |
|---------------|-------------|-------|
| New account | 40-60 | Moderate browsing |
| Established account | 80-100 | Standard |
| With Sales Navigator | 100-150 | Sales Nav expects more browsing |

**Profile view patterns:**
- Rapid sequential views (view 50 profiles in 10 minutes) trigger alerts
- Natural pattern: view a profile, spend 30-60 seconds, view next
- Mix profile views with other activities (reading feed, reacting to posts)

### Post Engagement (Likes and Comments)

| Action | Daily Limit | Notes |
|--------|-------------|-------|
| Likes | 50-100 | Spread throughout the day |
| Comments | 20-40 | Must be unique and substantive |
| Shares | 5-10 | Sharing others' content |
| Original posts | 1-2 | Your own content |

**Comment quality:**
- Generic comments ("Great post!", "Thanks for sharing!") can trigger spam detection if repeated
- Substantive comments (2-3 sentences adding to the conversation) are safe and beneficial
- Commenting on the same person's posts repeatedly can look like stalking

### Search Queries

| Account Status | Daily Limit | Notes |
|---------------|-------------|-------|
| Free LinkedIn | 15-25 | LinkedIn limits free search heavily |
| Premium / Sales Navigator | 30-50 | More generous but still limited |

LinkedIn implements a "commercial use limit" on free accounts that restricts search after a certain number of queries per month. Sales Navigator removes this limit but still has soft daily caps.

---

## Weekly Limits

| Action | Weekly Limit | Notes |
|--------|-------------|-------|
| Connection requests | 100-125 | 5 days of sending, 2 rest days |
| Messages | 250-350 | Includes all conversations |
| Profile views | 400-500 | Across the week |
| Total engagement actions | 500-700 | Combined likes, comments, shares |

### Pending Invitation Management

**Critical limit:** Keep total pending (unaccepted) connection requests below 1,000.

LinkedIn restricts accounts with too many pending invitations. This indicates you are sending requests that people do not want.

**Management strategy:**
- Withdraw pending requests older than 14 days
- Review weekly: if acceptance rate is below 25%, pause and improve targeting
- Never let pending count exceed 500 (even though the hard limit is higher)
- Withdrawing requests does count as activity -- don't withdraw 100 at once

---

## Account Warmup Schedule

For a new LinkedIn account or an account that has been mostly dormant:

### Week 1: Foundation

| Day | Activity | Volume |
|-----|----------|--------|
| Mon | Complete profile (photo, headline, about, experience), browse feed | 0 requests |
| Tue | Connect with 5 people you know personally, like 10 posts, comment on 3 | 5 requests |
| Wed | Browse profiles (20-30), like 10 posts, comment on 3 | 0 requests |
| Thu | Connect with 5 people you know, share 1 article | 5 requests |
| Fri | Browse feed, like 15 posts, comment on 5 | 0 requests |
| Sat-Sun | Light browsing only (5-10 minutes) | 0 requests |
| **Weekly total** | | **10 connection requests** |

### Week 2: Building

| Day | Activity | Volume |
|-----|----------|--------|
| Mon | 8 connection requests (with notes), browse feed, 10 likes | 8 requests |
| Tue | 8 connection requests, 5 messages to connections, 10 likes | 8 requests |
| Wed | 5 connection requests, post original content, 15 likes, 5 comments | 5 requests |
| Thu | 10 connection requests, 5 messages, browse profiles | 10 requests |
| Fri | 5 connection requests, 10 likes, 3 comments | 5 requests |
| Sat-Sun | Light browsing, 5 likes | 0 requests |
| **Weekly total** | | **36 connection requests** |

### Week 3: Expanding

| Day | Activity | Volume |
|-----|----------|--------|
| Mon | 12 connection requests, 10 messages, 15 likes | 12 requests |
| Tue | 12 connection requests, 10 messages, 10 likes, 5 comments | 12 requests |
| Wed | 10 connection requests, post content, 20 likes | 10 requests |
| Thu | 15 connection requests, 15 messages, 10 likes | 15 requests |
| Fri | 10 connection requests, 10 messages, 5 comments | 10 requests |
| Sat-Sun | Light browsing | 0 requests |
| **Weekly total** | | **59 connection requests** |

### Week 4+: Full Operation

| Day | Activity | Volume |
|-----|----------|--------|
| Mon | 20 connection requests, 15 messages, 20 likes, 5 comments | 20 requests |
| Tue | 20 connection requests, 15 messages, 15 likes, 5 comments | 20 requests |
| Wed | 15 connection requests, 20 messages, post content, 20 likes | 15 requests |
| Thu | 20 connection requests, 15 messages, 15 likes, 5 comments | 20 requests |
| Fri | 15 connection requests, 10 messages, 10 likes | 15 requests |
| Sat-Sun | Light browsing, occasional like | 0 requests |
| **Weekly total** | | **90-100 connection requests** |

**Important:** Even at full operation, take 1-2 "light days" per week where activity is 50% of normal. This mimics natural human behavior (busy days, lighter days).

---

## Timing Patterns

### Operating Hours

All LinkedIn activity should occur during plausible business hours in your timezone:

| Time Window | Activity Level | Notes |
|-------------|---------------|-------|
| 6:00-7:59 AM | Light | Some people check LinkedIn early, but keep it light |
| 8:00-11:00 AM | Peak | Highest engagement window, best time for connection requests |
| 11:00 AM-12:00 PM | Moderate | Pre-lunch wind-down |
| 12:00-1:00 PM | Light | Lunch break -- people browse but don't engage heavily |
| 1:00-4:00 PM | Peak | Second engagement window, good for messages |
| 4:00-6:00 PM | Moderate | End of day, people checking messages |
| 6:00-9:00 PM | Very Light | Occasional activity only (mimics evening check) |
| 9:00 PM-6:00 AM | None | No activity during sleep hours |

### Activity Spacing

**Do not batch activities.** Sending 20 connection requests in 5 minutes is a red flag.

**Natural spacing:**
- Connection requests: 2-5 minute gaps between requests (random, not fixed)
- Messages: 1-3 minute gaps
- Profile views: 30-90 seconds between views
- Likes: 5-15 seconds between likes
- Comments: 2-5 minutes between comments (you need time to "read" and "think")

**Random variation is critical.** If you send a connection request exactly every 3 minutes, it is obviously automated. Introduce randomness:
```
delay = base_delay + random(0, base_delay * 0.5)
# e.g., base 3 minutes: actual delay varies from 3.0 to 4.5 minutes
```

### Day-of-Week Patterns

| Day | Recommended Activity Level |
|-----|--------------------------|
| Monday | 80% of max (people are catching up from weekend) |
| Tuesday | 100% of max (highest LinkedIn engagement day) |
| Wednesday | 100% of max |
| Thursday | 90% of max |
| Friday | 60% of max (people wind down) |
| Saturday | 10% of max (occasional browsing only) |
| Sunday | 0-10% of max (rest day) |

---

## IP Address Considerations

### Residential IP (Home/Office Network)

**This is the safest option.** LinkedIn expects users to access from a consistent residential IP.

- Use your home or office internet connection
- IP should be in the same geographic region as your LinkedIn profile location
- Consistent IP over time builds trust (LinkedIn learns your pattern)

### VPN Usage

**Proceed with caution:**
- Avoid VPNs that assign datacenter IPs (LinkedIn blocks these)
- If you must use VPN, use one with residential IP addresses
- Keep VPN location consistent (always same city)
- Avoid switching VPN locations frequently (this triggers security verification)
- LinkedIn may require phone verification if it detects a new IP/location

### Datacenter IPs

**Never use datacenter IPs for LinkedIn.** This includes:
- AWS, Google Cloud, Azure instances
- DigitalOcean, Linode, Vultr VPS
- Any cloud-hosted automation running headless browsers
- Shared hosting IP addresses

LinkedIn maintains blocklists of known datacenter IP ranges. Using these triggers immediate security checks or blocks.

### Mobile Data

**Safe to use occasionally.** Mobile IPs are residential by nature. However:
- IP changes with each session (carrier assigns dynamic IPs)
- Frequent IP changes can trigger verification
- Use as supplement to your primary connection, not primary

---

## Profile Optimization for Safety

A complete, professional profile gets more leeway from LinkedIn's algorithms and higher acceptance rates from targets:

### Profile Completeness Checklist

- [ ] **Professional headshot** (clear face photo, professional setting)
- [ ] **Headline** (descriptive, not salesy -- "Marketing Agency Owner | Helping Local Businesses Grow" not "I'll 10x Your Revenue!")
- [ ] **About section** (300+ words, tells your story, mentions who you help)
- [ ] **Current position** (with company page linked)
- [ ] **Work history** (at least 2-3 positions)
- [ ] **Education** (school, degree)
- [ ] **Skills** (10+ skills added, endorsements from connections)
- [ ] **Recommendations** (3+ given and received)
- [ ] **Location** (matches your actual location)
- [ ] **Profile URL** (customized, e.g., linkedin.com/in/yourname)
- [ ] **Banner image** (custom, professional -- not LinkedIn default)
- [ ] **Featured section** (1-3 pieces: article, website, case study)
- [ ] **500+ connections** (builds credibility and social proof)

### Social Selling Index (SSI)

LinkedIn scores every account on a "Social Selling Index" (0-100) based on four factors:
1. Establish your professional brand (complete profile, post content)
2. Find the right people (use search, view profiles in your industry)
3. Engage with insights (like, comment, share relevant content)
4. Build relationships (connect with prospects, message connections)

**Check your SSI:** https://www.linkedin.com/sales/ssi

**Target SSI:** 60+ (indicates an active, engaged account that LinkedIn rewards with more visibility and fewer restrictions)

---

## Warning Signs and Detection Indicators

### LinkedIn Warnings

| Warning Sign | Severity | What It Means | Immediate Action |
|-------------|----------|---------------|-----------------|
| CAPTCHA challenge | Low-Medium | LinkedIn suspects automation | Solve CAPTCHA, reduce activity by 50% for 3 days |
| "You've reached the weekly invitation limit" | Medium | Exceeded connection request threshold | Stop all requests for 7 days |
| "We've noticed some unusual activity" | Medium-High | Pattern detection triggered | Stop ALL automation for 7-14 days |
| Phone verification required | Medium | New location/device detected | Verify phone, resume cautiously |
| Email verification required | Low | Standard security check | Verify email, no concern |
| Account restricted (temporary) | High | Multiple policy violations detected | Stop everything for 2-4 weeks |
| Identity verification (ID upload) | High | Suspected fake/misused account | Submit real ID, wait for review |
| Account suspended | Critical | Serious violations | Appeal via LinkedIn help, may be permanent |

### Self-Monitoring Checklist (Run Daily)

- [ ] Connection requests sent today: ___ (should be < daily limit)
- [ ] Messages sent today: ___ (should be < daily limit)
- [ ] Profile views today: ___ (should be < daily limit)
- [ ] Pending connection requests total: ___ (should be < 500)
- [ ] Any CAPTCHA challenges today? (if yes, reduce activity)
- [ ] Any LinkedIn warnings or messages? (if yes, stop and investigate)
- [ ] Connection request acceptance rate this week: ___% (should be > 25%)
- [ ] Message response rate this week: ___% (should be > 15%)

---

## Recovery Protocol

### If You Receive a Temporary Restriction

**Day 1-3:**
- Stop ALL automated activity immediately
- Do not log into LinkedIn more than once per day
- Only activity: browse feed passively for 5-10 minutes
- Do not send any messages or connection requests

**Day 4-7:**
- Light manual activity only
- Like 5-10 posts per day
- View 10-15 profiles per day
- No connection requests, no messages

**Week 2:**
- Resume light messaging (5-10 messages per day to existing connections)
- Resume connection requests at 50% warmup level (5-8 per day)
- Continue regular feed engagement

**Week 3:**
- Gradually increase to 75% of normal activity
- Monitor for any further warnings

**Week 4+:**
- Resume normal activity if no further warnings
- Reduce maximum limits by 20% from pre-restriction levels (permanently)

### If Your Account Is Suspended

1. Do not create a new account (LinkedIn detects and bans these quickly)
2. Submit an appeal through LinkedIn Help Center
3. In the appeal, explain that you did not use automation (even if you did -- LinkedIn does not verify this)
4. Be patient -- appeals can take 1-4 weeks
5. If reinstated, treat the account as brand new (full warmup from Week 1)
6. Permanently reduce all limits by 30-50%

---

## Monitoring Dashboard

### Airtable/Supabase Tracking Table

```
LinkedIn Activity Log:
- Date
- Connection Requests Sent (count)
- Connection Requests Accepted (count)
- Messages Sent (count)
- Messages Received (count)
- Profile Views (count)
- Likes (count)
- Comments (count)
- Posts Published (count)
- Warnings Received (text, if any)
- Notes
```

### Automated Alerts

| Alert | Trigger | Action |
|-------|---------|--------|
| Approaching daily connection limit | >20 requests sent today | Warn operator, block further sends |
| Approaching daily message limit | >50 messages sent today | Warn operator |
| Low acceptance rate | <20% this week | Review targeting, improve notes |
| Pending request buildup | >300 pending | Withdraw oldest pending requests |
| Warning detected | Any LinkedIn warning | Stop all automation, alert operator |
| IP change detected | IP differs from baseline | Alert operator, verify it was intentional |

### Weekly Performance Review

Every Monday, review the previous week's metrics:

1. Were all daily limits respected? (Yes/No)
2. Any warnings or restrictions? (Yes/No)
3. Acceptance rate trend (up/down/stable)
4. Response rate trend (up/down/stable)
5. Any messages reported as spam? (Yes/No)
6. Pending request count (should be decreasing if withdrawing old ones)
7. SSI score change (should be stable or increasing)

Use this review to adjust strategy. If any metric trends negative for two consecutive weeks, reduce activity levels and investigate root cause.

# Deploying AI Chatbot on WordPress and Google Business Profile

## Overview

This document covers deploying an AI chatbot widget on Steven's WordPress site and integrating chat capabilities with his Google Business Profile (GBP) presence. The chatbot serves as a 24/7 lead capture and qualification tool for SW Recovery Services, handling initial inquiries, answering FAQs about debt recovery processes, and routing qualified leads to the sales team.

**Critical update (as of July 2024):** Google Business Messages (GBM) was permanently discontinued on July 31, 2024. Google did not introduce a direct replacement. This significantly changes the GBP chatbot strategy -- we now focus on alternative approaches for capturing leads from Google Search and Maps visitors.

### Goals
- Deploy a custom AI chatbot on the WordPress site that reflects SW Recovery's brand and processes
- Maximize lead capture from Google Search/Maps visitors despite GBM deprecation
- Maintain conversation context and hand off to human agents when needed
- Integrate chat data with Nutshell CRM and Supabase for unified lead tracking

---

## API/Integration Details

### WordPress Chatbot Deployment Options

#### Option A: Custom Embed Widget (Recommended)

Build a custom chat widget using our own AI backend (OpenAI/Claude API) and embed it on WordPress. This gives full control over the conversational logic, branding, and data flow.

**Architecture:**
```
[WordPress Site]
    -> [Chat Widget (JS/iframe)]
        -> [Backend API (n8n or custom Node.js)]
            -> [LLM (OpenAI/Claude)]
            -> [Supabase (conversation storage)]
            -> [Nutshell CRM (lead creation)]
```

**Embedding methods:**

1. **Custom HTML/JS widget (preferred):**
   ```html
   <!-- Add to WordPress footer via theme customizer or plugin -->
   <script src="https://chat.swrecovery.com/widget.js"
           data-bot-id="sw-recovery-main"
           data-position="bottom-right"
           data-primary-color="#1a3d5c"
           async defer></script>
   ```

2. **WordPress shortcode (for specific pages):**
   ```php
   // In theme's functions.php
   function sw_chatbot_shortcode($atts) {
       $atts = shortcode_atts(['page' => 'default'], $atts);
       return '<div id="sw-chatbot" data-page="' . esc_attr($atts['page']) . '"></div>
               <script src="https://chat.swrecovery.com/widget.js" async></script>';
   }
   add_shortcode('sw_chatbot', 'sw_chatbot_shortcode');
   ```
   Usage: `[sw_chatbot page="services"]`

3. **iframe embed (simplest isolation):**
   ```html
   <iframe src="https://chat.swrecovery.com/embed"
           style="position:fixed;bottom:20px;right:20px;width:380px;height:520px;border:none;z-index:9999;">
   </iframe>
   ```

**Communication protocol -- WebSocket vs Polling:**

| Factor | WebSocket | Long Polling | SSE (Server-Sent Events) |
|--------|-----------|-------------|--------------------------|
| Latency | Lowest (real-time) | Medium (1-3s) | Low (real-time receive) |
| Complexity | Higher | Lower | Medium |
| Server load | Lower (persistent) | Higher (repeated connections) | Medium |
| Firewall compatibility | Sometimes blocked | Always works | Usually works |
| Best for | Real-time back-and-forth | Simple Q&A | Streaming LLM responses |

**Recommendation:** Use **SSE for LLM response streaming** (matches how ChatGPT-style interfaces work) with a REST API for sending messages. This avoids WebSocket complexity while providing a responsive feel. Fall back to standard REST request/response if SSE is blocked.

#### Option B: Third-Party Chatbot Platform

Use an existing chatbot platform with WordPress plugin support.

**Viable platforms:**

| Platform | WordPress Integration | AI Capability | Monthly Cost | Pros | Cons |
|----------|----------------------|---------------|-------------|------|------|
| Voiceflow | Embed code / iframe | GPT-4, Claude | $50-100 | Visual builder, good NLU | Less data control |
| Landbot | WordPress plugin | GPT-4 integration | $40-100 | Drag-and-drop flows | Limited AI depth |
| CustomGPT | WordPress plugin | GPT-4 trained on site | $49-299 | Trains on your content | Less customizable UI |
| AI Engine (WP plugin) | Native plugin | OpenAI API | Free + API costs | Fully in WordPress | Plugin dependency |
| Tidio | WordPress plugin | Lyro AI | $29-59 | Live chat + AI hybrid | Brand watermark on free |

**Recommendation:** Option A (custom) for maximum control over lead qualification logic and CRM integration. Option B only if build time needs to be minimized.

### Google Business Profile -- Post-GBM Strategy

Since Google Business Messages was shut down July 2024, here are the alternative approaches for capturing leads from Google Search/Maps:

#### Strategy 1: Click-to-Chat via GBP Website Link

- Set the GBP website link to a dedicated landing page with the chatbot prominently displayed
- The landing page URL can include UTM parameters to track GBP traffic: `https://swrecovery.com/chat?utm_source=google&utm_medium=gbp`
- The chatbot auto-opens on this page with a GBP-specific greeting

#### Strategy 2: WhatsApp Business Integration

Google now supports WhatsApp as a messaging option on Business Profiles for eligible accounts.

**Setup:**
1. Create/verify WhatsApp Business account for SW Recovery
2. Link WhatsApp number to Google Business Profile
3. Connect WhatsApp Business API to our chatbot backend via n8n
4. AI handles initial WhatsApp conversations, escalates to human when needed

**Architecture:**
```
[Google Maps/Search] -> [WhatsApp Button on GBP]
    -> [WhatsApp Business API]
        -> [n8n webhook]
            -> [AI chatbot logic]
            -> [Nutshell CRM]
```

#### Strategy 3: Google Ads Chat Extensions

For paid search campaigns, Google Ads still supports message extensions that can route to various chat platforms.

#### Strategy 4: Click-to-Call with AI Voice Bot

Leverage the existing AI voice bot (already in the stack) as the primary GBP contact method. The GBP phone number routes to the AI voice bot for initial screening and qualification.

**This is the most practical approach** given that the voice bot is already being built and Google Maps/Search users frequently prefer calling.

### Chat Widget Technical Requirements

**Frontend (widget.js):**
- Vanilla JS or lightweight framework (Preact ~3KB)
- Lazy-loaded after page load (no impact on Core Web Vitals)
- Responsive: full-width on mobile, fixed panel on desktop
- Accessibility: ARIA labels, keyboard navigation, screen reader support
- Offline handling: queue messages if connection drops, send when restored
- Cookie consent: integrate with WordPress cookie consent plugin

**Backend API endpoints:**
```
POST /api/chat/start          -- Initialize conversation, get session ID
POST /api/chat/message        -- Send user message, receive AI response (SSE)
GET  /api/chat/history/{id}   -- Retrieve conversation history
POST /api/chat/handoff        -- Escalate to human agent
POST /api/chat/lead           -- Create/update lead in CRM
```

**Data storage (Supabase):**
```sql
CREATE TABLE chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT UNIQUE NOT NULL,
    visitor_ip TEXT,
    source TEXT, -- 'website', 'gbp-landing', 'whatsapp'
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    lead_id TEXT, -- Nutshell CRM lead ID
    status TEXT DEFAULT 'active' -- active, completed, escalated
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES chat_conversations(id),
    role TEXT NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Implementation Approach

### Phase 2 Build Plan

#### Step 1: Chat Backend Setup
1. Create chat API endpoints (Node.js or n8n HTTP endpoints)
2. Configure LLM connection (OpenAI GPT-4o or Claude) with SW Recovery system prompt
3. Train on SW Recovery FAQs, services, pricing guidance, and qualification criteria
4. Set up Supabase tables for conversation storage
5. Implement lead qualification logic:
   - Debt amount threshold routing (matches voice bot logic)
   - Contact info capture
   - Auto-create lead in Nutshell CRM when qualified

#### Step 2: WordPress Widget Deployment
1. Build the chat widget (JS bundle, <50KB gzipped)
2. Host widget assets on CDN or the chat backend server
3. Add embed code to WordPress via:
   - Theme customizer > Additional JavaScript (site-wide)
   - Or "Insert Headers and Footers" plugin for easier management
4. Test on all key pages: homepage, services, contact, blog posts
5. Verify mobile responsiveness and page speed impact

#### Step 3: GBP Lead Capture Setup
1. Create dedicated landing page: `/chat` or `/get-help`
2. Configure GBP website link to point to this page
3. Set up WhatsApp Business (if Steven wants this channel)
4. Ensure GBP phone number routes to AI voice bot
5. Track all GBP-sourced conversations with UTM tagging

#### Step 4: CRM Integration
1. When chatbot qualifies a lead, auto-create in Nutshell via API
2. Attach conversation transcript to the Nutshell lead
3. Tag lead source (website-chat, gbp-landing, whatsapp)
4. Trigger Slack notification for high-value leads requiring immediate human follow-up

#### Step 5: Analytics and Optimization
1. Track: conversations started, messages per session, lead conversion rate, escalation rate
2. Log all conversations to Supabase for review and AI training improvement
3. A/B test chatbot greetings and qualification flows
4. Monthly review of common questions to improve knowledge base

### WordPress Performance Considerations

- **Lazy-load the widget:** Load `widget.js` with `defer` or after `DOMContentLoaded`
- **Minimal DOM footprint:** Single root div, shadow DOM if possible to avoid CSS conflicts
- **No jQuery dependency:** Use vanilla JS to avoid loading jQuery if the theme doesn't use it
- **CDN hosting:** Serve widget assets from a CDN (Cloudflare, BunnyCDN) for fast global delivery
- **GDPR/CCPA compliance:** Show cookie consent before storing any conversation data; provide data deletion API

---

## Cost Implications

### Option A: Custom Build

| Item | Cost | Notes |
|------|------|-------|
| LLM API (OpenAI GPT-4o) | $20-80/month | ~500-2,000 conversations/month at ~$0.04 each |
| LLM API (Claude Sonnet) | $15-60/month | Alternative, similar pricing |
| Supabase (conversation storage) | $0-25/month | Free tier covers initial volume |
| CDN for widget assets | $0-5/month | Cloudflare free tier usually sufficient |
| WhatsApp Business API | $0-50/month | Per-conversation pricing after 1,000 free/month |
| **Total (custom)** | **$35-170/month** | Scales with conversation volume |

### Option B: Third-Party Platform

| Platform | Monthly Cost | Includes |
|----------|-------------|----------|
| Voiceflow Pro | $50/month | 1,000 AI interactions |
| Tidio+ | $59/month | Lyro AI + live chat |
| CustomGPT Business | $99/month | Trained on site content |
| Landbot Pro | $100/month | WhatsApp + web |

### One-Time Costs

| Item | Cost |
|------|------|
| WhatsApp Business verification | $0 (free) |
| GBP landing page design | Included in website build |

---

## Estimated Build Hours

### Option A: Custom Chatbot Widget

| Task | Hours | Notes |
|------|-------|-------|
| Chat backend API development | 8 | Endpoints, LLM integration, session management |
| AI system prompt and knowledge base | 4 | SW Recovery-specific training, qualification logic |
| Chat widget frontend | 10 | JS widget, UI/UX, responsive design, accessibility |
| WordPress integration and testing | 3 | Embed code, page speed verification, cross-browser |
| Supabase schema and data layer | 2 | Tables, RLS policies, indexes |
| Nutshell CRM integration | 3 | Lead creation, transcript attachment |
| GBP landing page | 2 | Dedicated page with auto-open chatbot |
| WhatsApp Business setup | 4 | API connection, n8n workflow, testing |
| Analytics dashboard | 2 | Conversation metrics in Supabase/dashboard |
| Testing and QA | 4 | End-to-end testing across devices and sources |
| **Total (custom)** | **42** | |

### Option B: Third-Party Platform

| Task | Hours | Notes |
|------|-------|-------|
| Platform selection and setup | 2 | Account creation, initial config |
| AI training and knowledge base | 4 | Upload FAQs, test conversations |
| WordPress plugin installation | 1 | Install, configure, style |
| CRM integration | 3 | Webhook to Nutshell |
| GBP landing page | 2 | Same as Option A |
| Testing | 2 | Cross-device, conversation flows |
| **Total (third-party)** | **14** | |

**Recommendation:** Start with Option B (third-party) for faster deployment in Phase 2, then migrate to Option A (custom) in Phase 3 if deeper control is needed. The GBP strategy should prioritize the AI voice bot as the primary contact method, with the website chatbot as secondary.

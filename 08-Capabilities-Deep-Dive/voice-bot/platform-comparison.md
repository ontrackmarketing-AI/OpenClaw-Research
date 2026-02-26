# AI Voice Bot Platform Comparison

## Overview

This document provides a deep comparison of the four leading AI voice bot platforms for SW Recovery Services' inbound call automation system. The voice bot is **inbound only** with a single number for all inflow, routing by deal size and department across 20 employees, with 24/7 answering and a 2-second response target.

Each platform is evaluated on: pricing, latency, STT/TTS engine options, customization, API quality, scalability, and reliability.

---

## Platform Summaries

### 1. Vapi AI

**Category**: Developer-first voice AI orchestration platform

Vapi is a developer-focused platform for building advanced voice AI agents. It provides sub-500ms latency, Squads (multi-agent orchestration), and integrates with 40+ apps including CRMs, calendars, and workflow tools.

**Strengths**:
- Squads architecture for multi-agent handoffs (greeting agent -> routing agent -> specialist)
- Native Google Calendar integration for appointment booking
- Knowledge Base (RAG) support -- upload PDFs/docs for real-time reference
- Function calling for mid-call API triggers (CRM updates, SMS, email)
- 1M+ concurrent call capacity
- Telephony via Twilio, Vonage, or Telnyx

**Weaknesses**:
- Requires developer expertise; no visual builder for non-technical users
- Hidden costs -- 4-6 provider contracts needed for production
- Debugging multi-agent flows can be complex

### 2. Retell AI

**Category**: LLM-first conversational AI phone agent platform

Retell AI focuses on natural, human-like conversations powered by frontier LLMs (GPT-4.1, Claude). It offers bundled pricing, SOC 2/HIPAA compliance, and dynamic knowledge base auto-sync.

**Strengths**:
- Bundled pricing simplifies billing vs. Vapi's multi-vendor model
- Dynamic knowledge base with auto-crawling and instant policy updates
- Cal.com preset tools for calendar integration (check availability, book appointments)
- SOC 2, HIPAA, and GDPR compliance out of the box
- Unlimited concurrency and batch calling at scale
- CRM integrations with Salesforce, HubSpot, Zendesk built-in

**Weaknesses**:
- No full visual builder or real-time testing UI
- Lacks enterprise controls like RBAC and role-specific environments
- Less flexible multi-agent orchestration compared to Vapi Squads

### 3. Bland AI

**Category**: Developer-first programmable voice calling API

Bland AI provides a programmatic API for building voice agents that make and receive calls, with voice cloning, real-time scripting, and webhook-based CRM sync.

**Strengths**:
- Free tier: 100 calls/day, 10 concurrent
- Voice cloning for brand consistency
- Conversational Pathways for visual flow design
- Post-call webhooks for real-time CRM sync
- Real-time API requests during calls (calendar checks, database lookups)
- Emotion control (pitch, speed adjustment)

**Weaknesses**:
- Less mature ecosystem than Vapi or Retell
- Multi-agent handoff less sophisticated than Vapi Squads
- Calendar booking requires Zapier/webhook intermediary (not native)
- Documentation less comprehensive

### 4. Twilio Voice + ConversationRelay (Custom Build)

**Category**: Telephony infrastructure with AI orchestration layer

Twilio provides the raw telephony infrastructure (ConversationRelay) that integrates STT, TTS, and LLM orchestration via WebSocket API. Maximum control, maximum complexity.

**Strengths**:
- Full control over every component (STT engine, TTS engine, LLM, routing logic)
- ConversationRelay simplifies WebSocket orchestration vs. raw Media Streams
- Enterprise-grade reliability and global scale
- No vendor lock-in on AI components
- Deepest telephony feature set (call recording, DTMF, SIP trunking)

**Weaknesses**:
- Requires significant engineering investment (months vs. weeks)
- Must build and maintain multi-agent orchestration from scratch
- No built-in knowledge base, calendar, or CRM integrations
- Higher ongoing maintenance burden

---

## Pricing Comparison

| Component | Vapi AI | Retell AI | Bland AI | Twilio Custom |
|-----------|---------|-----------|----------|---------------|
| **Platform fee** | $0.05/min | $0.07-0.08/min | $0.09/min | $0.07/min (ConversationRelay) |
| **LLM cost** | $0.006-0.10/min (varies by model) | Bundled in platform | Bundled in platform | Direct provider pricing |
| **Telephony** | $0.008-0.014/min (Twilio/Vonage) | $0.015/min (Twilio) | Included | $0.0085-0.014/min |
| **STT/TTS** | Separate (provider-dependent) | Bundled | Bundled | Separate (provider-dependent) |
| **Total estimated** | **$0.13-0.31/min** | **$0.13-0.31/min** | **$0.09-0.15/min** | **$0.10-0.25/min** |
| **1,000 min/month** | ~$130-310 | ~$130-310 | ~$90-150 | ~$100-250 |
| **10,000 min/month** | ~$1,300-3,100 | ~$1,200-1,800 (enterprise) | ~$900-1,500 | ~$1,000-2,500 |
| **Enterprise discount** | Custom | $0.05+/min base | Custom | Volume pricing |
| **Healthcare BAA** | $1,000/mo add-on | Included (HIPAA) | N/A | Available |

### Monthly Plan Options (Bland AI)
- **Free**: 100 calls/day, 10 concurrent
- **Build**: $299/mo
- **Scale**: $499/mo
- **Enterprise**: Custom (unlimited calls, concurrency, voice clones)

---

## Latency Comparison

| Metric | Vapi AI | Retell AI | Bland AI | Twilio Custom |
|--------|---------|-----------|----------|---------------|
| **Advertised latency** | Sub-500ms | ~500ms | Sub-second | Depends on pipeline |
| **First response time** | ~600ms | ~500-800ms | ~800ms-1s | ~1.1s (unoptimized) |
| **Streaming support** | Yes | Yes | Yes | Yes (WebSocket) |
| **Turn-taking** | Natural | Natural | Natural | Must implement |
| **Barge-in handling** | Built-in | Built-in | Built-in | Must implement |
| **2-second SLA feasible** | Yes | Yes | Yes | Yes (with optimization) |

### Latency Pipeline Breakdown (typical)
- STT: 100-350ms
- LLM inference: 200-500ms (60-70% of total)
- TTS: 75-300ms (ElevenLabs Flash v2.5 = 75ms)
- Network/overhead: 40-100ms
- **Total unoptimized**: ~800ms-1.9s
- **Total with streaming**: ~400-800ms

---

## STT/TTS Engine Support

| Engine | Vapi AI | Retell AI | Bland AI | Twilio Custom |
|--------|---------|-----------|----------|---------------|
| **Deepgram (STT)** | Yes | Yes | Yes | Yes |
| **OpenAI Whisper (STT)** | Yes | Yes | Via API | Yes |
| **Google STT** | Yes | Yes | Limited | Yes |
| **ElevenLabs (TTS)** | Yes | Yes | Yes | Yes |
| **OpenAI TTS** | Yes | Yes | Yes | Yes |
| **PlayHT (TTS)** | Yes | Yes | Limited | Yes |
| **Azure TTS** | Yes | Yes | Limited | Yes |
| **Voice cloning** | Via providers | Via providers | Native | Via providers |
| **Custom voices** | Yes | Yes | Yes (unlimited on Enterprise) | Yes |

---

## Multi-Agent / Routing Capabilities

| Feature | Vapi AI | Retell AI | Bland AI | Twilio Custom |
|---------|---------|-----------|----------|---------------|
| **Multi-agent orchestration** | Squads (native) | Transfer tools | Conversational Pathways | Must build |
| **Context handoff control** | None / Last N / All | Configurable | Via webhooks | Must build |
| **Department routing** | Via prompts + tools | Via LLM routing | Via API logic | Full control |
| **Deal size routing** | Function calling + CRM lookup | Tool calling + CRM | Webhook + CRM lookup | Full control |
| **Warm transfer** | Yes | Yes | Yes | Yes |
| **Cold transfer** | Yes | Yes | Yes | Yes |
| **DTMF support** | Yes | Limited | Yes | Full |
| **After-hours logic** | Via prompts | Via configuration | Via API | Full control |

---

## Integration Ecosystem

| Integration | Vapi AI | Retell AI | Bland AI | Twilio Custom |
|-------------|---------|-----------|----------|---------------|
| **Google Calendar** | Native | Via Cal.com | Via Zapier/API | Via API |
| **Calendly** | Via n8n/Make | Via Zapier | Via Zapier | Via API |
| **Nutshell CRM** | Via Zapier/webhook | Via Zapier/webhook | Via Zapier/webhook | Via API |
| **HubSpot** | Native | Native | Via webhook | Via API |
| **Salesforce** | Via Zapier | Native | Via webhook | Via API |
| **Zapier** | Yes | Yes | Yes | Yes |
| **n8n** | Yes | Yes | Yes | Yes |
| **Make.com** | Yes | Yes | Yes | Yes |
| **Knowledge base (RAG)** | Native (PDF/TXT upload) | Native (auto-crawl) | Via API | Must build |
| **Call recording** | Yes | Yes | Yes | Native |
| **Call transcription** | Yes | Yes | Yes | Native |

---

## Recommendation for SW Recovery Services

### Primary Recommendation: Vapi AI

**Why Vapi wins for this use case**:

1. **Squads architecture** is purpose-built for the multi-agent routing SW Recovery needs:
   - Greeting agent qualifies caller intent
   - Routing agent checks deal size via CRM lookup (Nutshell)
   - $50M+/Fortune 500 -> warm transfer to Steven
   - Department routing -> transfer to appropriate employee
   - Scheduling agent books meetings via Google Calendar
   - After-hours agent takes messages and offers booking

2. **Sub-500ms latency** comfortably meets the 2-second response SLA

3. **Native Google Calendar integration** simplifies calendar booking without middleware

4. **Knowledge base (RAG)** allows uploading company docs, service descriptions, and FAQs

5. **Function calling** enables real-time CRM lookups mid-call for deal size routing

6. **Scale**: 1M+ concurrent calls means no capacity concerns as call volume grows

### Secondary Recommendation: Retell AI

Choose Retell if compliance is a top priority (SOC 2/HIPAA built-in) or if bundled pricing simplicity is preferred. The Cal.com integration provides solid calendar booking, and knowledge base auto-sync keeps information current.

### Not Recommended: Twilio Custom Build

While offering maximum control, the engineering investment (estimated 3-6 months) and ongoing maintenance burden make this impractical for the current timeline. The managed platforms provide 90%+ of the functionality at a fraction of the build cost.

---

## Cost Implications

### Estimated Monthly Costs (Vapi AI -- Primary Recommendation)

| Volume Tier | Platform | LLM | Telephony | STT/TTS | Total |
|-------------|----------|-----|-----------|---------|-------|
| **500 min/mo** (low) | $25 | $30-50 | $4-7 | $10-20 | **$70-100** |
| **2,000 min/mo** (medium) | $100 | $120-200 | $16-28 | $40-80 | **$275-410** |
| **5,000 min/mo** (high) | $250 | $300-500 | $40-70 | $100-200 | **$690-1,020** |
| **10,000 min/mo** (scale) | $500 | $600-1,000 | $80-140 | $200-400 | **$1,380-2,040** |

### One-Time Setup Costs
- Vapi account + telephony setup: $0
- Phone number provisioning: ~$2/mo
- n8n/Make.com for workflow automation: $20-50/mo
- Knowledge base document preparation: Internal labor

---

## Estimated Build Hours

| Phase | Hours | Description |
|-------|-------|-------------|
| Platform setup + telephony | 4-6h | Vapi account, Twilio number, basic config |
| Greeting + routing agent design | 8-12h | Prompts, tools, CRM lookup logic |
| Multi-agent Squad configuration | 12-16h | All agents, handoff logic, context management |
| Calendar booking integration | 6-8h | Google Calendar + Nutshell Scheduler |
| Knowledge base setup | 4-6h | Document preparation, upload, testing |
| After-hours flow | 4-6h | Voicemail, message taking, booking fallback |
| CRM integration (Nutshell) | 8-12h | Webhook setup, contact/lead sync |
| Testing + QA | 12-16h | All routing paths, edge cases, load testing |
| **Total** | **58-82h** | ~2-3 weeks with dedicated developer |

---

## Sources

- [Vapi AI Pricing](https://vapi.ai/pricing)
- [Vapi Squads Documentation](https://docs.vapi.ai/squads)
- [Vapi Google Calendar Integration](https://docs.vapi.ai/tools/google-calendar)
- [Retell AI Pricing](https://www.retellai.com/pricing)
- [Retell AI Knowledge Base](https://www.retellai.com/features/knowledge-base)
- [Retell AI Calendar Booking](https://www.retellai.com/features/book-appointments)
- [Bland AI Platform](https://www.bland.ai/)
- [Bland AI Pricing Guide](https://www.lindy.ai/blog/bland-ai-pricing)
- [Twilio ConversationRelay](https://www.twilio.com/en-us/products/conversational-ai/conversationrelay)
- [Twilio Voice Pricing](https://www.twilio.com/en-us/voice/pricing/us)
- [Voice AI Latency Optimization](https://www.ruh.ai/blogs/voice-ai-latency-optimization)

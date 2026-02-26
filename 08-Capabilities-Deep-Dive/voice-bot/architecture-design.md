# Voice Bot Architecture Design

## Overview

This document defines the inbound call flow architecture for SW Recovery Services' AI voice bot system. The system handles all inbound calls through a single phone number, routing by caller intent, deal size, and department -- with a hard 2-second response SLA. The architecture uses **Vapi AI Squads** as the recommended platform, with multi-agent orchestration, knowledge base integration, and real-time CRM lookups.

The bot is **inbound only** -- one number for all inflow. It must:
- Answer 24/7 with sub-2-second first response
- Route $50M+/Fortune 500 calls directly to Steven
- Route departmental calls to the appropriate employee (20 staff)
- Book meetings when staff are unavailable
- Take messages and handle after-hours scenarios
- Access company knowledge base for common questions

---

## Inbound Call Flow Architecture

### High-Level Flow Diagram

```
Incoming Call (Single Number)
    |
    v
[Twilio/Vonage Telephony]
    |
    v
[Vapi Squad Entry Point]
    |
    v
[Greeting Agent] -- "Thank you for calling SW Recovery Services..."
    |
    +--> Caller states intent
    |
    v
[Intent Classification]
    |
    +---> New Business / Deal Inquiry --> [Deal Qualification Agent]
    |                                          |
    |                                          +--> CRM Lookup (Nutshell API)
    |                                          +--> Ask qualifying questions
    |                                          +--> Determine deal size
    |                                          |
    |                                          v
    |                                     [Routing Decision]
    |                                          |
    |                                          +--> $50M+ / Fortune 500 --> Warm Transfer to Steven
    |                                          +--> $10M-$50M --> Transfer to Senior Rep
    |                                          +--> < $10M --> Transfer to Available Rep
    |                                          +--> No rep available --> [Scheduling Agent]
    |
    +---> Existing Client / Follow-up --> [Client Lookup Agent]
    |                                          |
    |                                          +--> CRM lookup by phone/name
    |                                          +--> Route to assigned rep
    |                                          +--> If unavailable --> [Scheduling Agent]
    |
    +---> Department Request --> [Department Router]
    |                               |
    |                               +--> "Accounting" --> Transfer to accounting
    |                               +--> "Legal" --> Transfer to legal team
    |                               +--> "Operations" --> Transfer to ops
    |                               +--> If unavailable --> [Scheduling Agent]
    |
    +---> General Questions --> [Knowledge Base Agent]
    |                               |
    |                               +--> Answer from RAG knowledge base
    |                               +--> Offer to connect with human if needed
    |
    +---> After Hours --> [After-Hours Agent]
                            |
                            +--> Take message
                            +--> Offer meeting booking
                            +--> Emergency escalation (on-call transfer)
```

---

## Multi-Agent Squad Design

### Agent 1: Greeting Agent (Entry Point)

**Role**: First point of contact. Qualifies caller intent within 5-10 seconds.

**Prompt Design**:
```
You are the receptionist for SW Recovery Services, a leading environmental
recovery and remediation company. Your job is to warmly greet callers and
quickly determine their purpose.

Classify the caller's intent into one of these categories:
- NEW_BUSINESS: New project inquiry, RFP, bid request, partnership
- EXISTING_CLIENT: Following up on existing project, status check
- DEPARTMENT: Requesting specific department or person
- GENERAL_QUESTION: Company info, services, hours, location
- EMERGENCY: Urgent environmental issue requiring immediate response

Once classified, hand off to the appropriate specialist agent.
Keep your greeting under 10 seconds. Be professional but warm.
```

**Tools Available**:
- `handoff_to_deal_qualification` (for NEW_BUSINESS)
- `handoff_to_client_lookup` (for EXISTING_CLIENT)
- `handoff_to_department_router` (for DEPARTMENT)
- `handoff_to_knowledge_base` (for GENERAL_QUESTION)
- `handoff_to_emergency` (for EMERGENCY)

**Context Passed**: All messages (caller intent is critical for downstream agents)

### Agent 2: Deal Qualification Agent

**Role**: Qualifies new business inquiries and determines deal size for routing.

**Prompt Design**:
```
You are a deal qualification specialist for SW Recovery Services.
Your job is to quickly gather key information about the caller's project:

1. Company name and caller name
2. Project type (remediation, recovery, environmental services)
3. Estimated project value or scope indicators
4. Timeline and urgency
5. Whether they are Fortune 500 or government entity

CRITICAL ROUTING RULES:
- If project value is $50M+ OR caller is Fortune 500: IMMEDIATELY warm transfer to Steven
- If project value is $10M-$50M: Route to senior recovery specialist
- If project value is under $10M: Route to available representative

Use the CRM lookup tool to check if this company already exists in Nutshell.
If no rep is available, offer to book a meeting.
```

**Tools Available**:
- `nutshell_crm_lookup` (check existing contacts/companies)
- `nutshell_create_lead` (create new lead with deal info)
- `warm_transfer_steven` (direct line to Steven)
- `transfer_to_rep` (transfer to specific employee)
- `handoff_to_scheduling` (if no one available)

### Agent 3: Client Lookup Agent

**Role**: Identifies existing clients and routes to their assigned representative.

**Tools Available**:
- `nutshell_contact_search` (by phone number, name, company)
- `nutshell_get_assigned_rep` (find who owns the account)
- `transfer_to_rep` (connect to assigned rep)
- `handoff_to_scheduling` (if rep unavailable)

### Agent 4: Department Router

**Role**: Routes to specific departments or individuals by name.

**Configuration**: Maintains a directory of 20 employees with:
- Name, extension, department, availability status
- Direct transfer numbers
- Backup contacts for each department
- Business hours per employee

### Agent 5: Knowledge Base Agent

**Role**: Answers general questions using RAG-powered knowledge base.

**Knowledge Base Contents**:
- Company services and capabilities
- Project types and specializations
- Office locations and hours
- Compliance certifications
- General pricing guidance (ranges, not specifics)
- FAQ document

### Agent 6: Scheduling Agent

**Role**: Books meetings when requested staff are unavailable.

**Tools Available**:
- `google_calendar_check_availability` (check rep's calendar)
- `google_calendar_book_meeting` (create calendar event)
- `nutshell_scheduler_link` (send Nutshell booking link via SMS)
- `send_confirmation_sms` (text confirmation to caller)

### Agent 7: After-Hours Agent

**Role**: Handles calls outside business hours.

**Capabilities**:
- Take detailed messages (name, company, purpose, urgency, callback number)
- Offer meeting booking for next business day
- Emergency escalation: warm transfer to on-call manager
- Send message summary to appropriate inbox via webhook

---

## 2-Second Response SLA Design

### Latency Budget Breakdown

The total time from when the caller stops speaking to when the bot starts responding must be under 2 seconds. Here is the latency budget:

| Stage | Target | Technique |
|-------|--------|-----------|
| **Voice Activity Detection (VAD)** | 30-50ms | Vapi built-in endpointing |
| **Audio buffering** | 30ms | Minimal buffer |
| **STT transcription** | 150-300ms | Deepgram Nova-2 (streaming) |
| **LLM inference** | 300-600ms | GPT-4o-mini or Claude 3.5 Haiku |
| **TTS synthesis** | 75-150ms | ElevenLabs Flash v2.5 or OpenAI TTS |
| **Network round-trip** | 40-80ms | US-based servers |
| **Total** | **625ms-1.2s** | Well within 2s SLA |

### Optimization Strategies

**STT Optimization**:
- Use Deepgram Nova-2 with streaming mode (transcribes as caller speaks)
- Enable endpointing at 200ms silence threshold (balances speed vs. premature cutoff)
- Disable punctuation/formatting for speed (post-process if needed)

**LLM Optimization**:
- Use GPT-4o-mini for routing decisions (fastest, cheapest)
- Use GPT-4o or Claude 3.5 Sonnet only for complex knowledge base queries
- Implement prompt caching for repeated queries (80% latency reduction)
- Keep system prompts under 1,000 tokens for each agent
- Pre-compute routing rules as tool definitions, not prompt instructions

**TTS Optimization**:
- Use ElevenLabs Flash v2.5 (75ms synthesis time) or OpenAI TTS
- Stream TTS audio chunks (start playing before full synthesis completes)
- Pre-cache common phrases ("Please hold while I transfer you...")

**Architecture Optimization**:
- Streaming pipeline: STT streams to LLM as words arrive, LLM streams to TTS
- Eliminates sequential wait times between stages
- Filler phrases during CRM lookups: "Let me check on that for you..."
- Parallel processing: Start CRM lookup while still processing caller speech

### Fallback for Latency Spikes

If response latency exceeds 1.5 seconds:
1. Play filler audio: "One moment please..." / "Let me look into that..."
2. If exceeds 3 seconds: "I apologize for the brief delay, I'm pulling up your information now."
3. If system is degraded: Offer to take a message or transfer to live operator

---

## STT/TTS Engine Selection

### Recommended STT: Deepgram Nova-2

| Criteria | Deepgram Nova-2 | OpenAI Whisper | Google STT |
|----------|-----------------|----------------|------------|
| **Latency** | 150-250ms (streaming) | 300-500ms (batch) | 200-350ms |
| **Accuracy** | 94-96% | 95-97% | 93-95% |
| **Streaming** | Yes (real-time) | No (batch only) | Yes |
| **Cost** | $0.0043/min | $0.006/min | $0.006/min |
| **Background noise** | Excellent | Good | Good |
| **Accents/dialects** | Excellent | Excellent | Good |

**Choice**: Deepgram Nova-2 for best latency-to-accuracy ratio with streaming support.

### Recommended TTS: ElevenLabs Flash v2.5

| Criteria | ElevenLabs Flash | OpenAI TTS | PlayHT |
|----------|------------------|------------|--------|
| **Latency** | 75ms | 100-200ms | 150-300ms |
| **Voice quality** | Excellent | Very good | Good |
| **Voice cloning** | Yes | No | Yes |
| **Streaming** | Yes | Yes | Yes |
| **Cost** | $0.18/1K chars | $0.015/1K chars | $0.10/1K chars |
| **Emotion control** | Yes | Limited | Yes |

**Choice**: ElevenLabs Flash v2.5 for lowest latency and highest voice quality. OpenAI TTS as cost-effective backup for non-critical paths.

---

## Knowledge Base Integration

### Architecture

```
[Caller Question]
    |
    v
[Knowledge Base Agent receives transcribed question]
    |
    v
[Vapi RAG Tool]
    |
    +--> Semantic search across uploaded documents
    +--> Returns top 3-5 relevant chunks
    |
    v
[LLM generates answer from retrieved context]
    |
    v
[TTS delivers answer to caller]
```

### Document Preparation

| Document Type | Format | Update Frequency |
|---------------|--------|------------------|
| Company overview & services | PDF | Quarterly |
| Service area capabilities | PDF | Quarterly |
| Pricing guidance (ranges) | TXT | Monthly |
| Employee directory | JSON/TXT | As needed |
| FAQ | TXT | Monthly |
| Compliance/certifications | PDF | Annually |
| Office hours/locations | TXT | As needed |

### RAG Configuration
- **Chunk size**: 500-800 tokens (balance between context and relevance)
- **Overlap**: 100 tokens between chunks
- **Top-K retrieval**: 3-5 chunks per query
- **Similarity threshold**: 0.7 minimum (avoid hallucination from low-relevance matches)
- **Fallback**: If no relevant chunks found, offer to connect with human agent

---

## Conversation Context Management

### Handoff Strategy Between Agents

| Handoff | Context Passed | Rationale |
|---------|---------------|-----------|
| Greeting -> Deal Qualification | All messages | Full context needed for qualification |
| Greeting -> Client Lookup | All messages | Need caller's stated identity |
| Greeting -> Department Router | Last 3 messages | Only need department/name request |
| Any Agent -> Scheduling | Last 5 messages + metadata | Need person requested + reason |
| Any Agent -> After-Hours | All messages | Full context for message-taking |
| Any Agent -> Live Transfer | All messages (summary injected) | Human needs full picture |

### Context Metadata Passed Between Agents

```json
{
  "caller_phone": "+15551234567",
  "caller_name": "John Smith",
  "company_name": "Acme Corp",
  "intent": "NEW_BUSINESS",
  "deal_size_estimate": "$25M",
  "is_fortune_500": false,
  "requested_person": null,
  "requested_department": "sales",
  "urgency": "normal",
  "nutshell_contact_id": "12345",
  "nutshell_lead_id": null,
  "call_start_time": "2026-02-13T10:30:00Z",
  "is_after_hours": false
}
```

---

## System Reliability

### Failover Architecture

1. **Primary**: Vapi AI + Twilio telephony
2. **Telephony failover**: Vonage as backup carrier (auto-failover via Vapi)
3. **LLM failover**: GPT-4o-mini primary -> Claude 3.5 Haiku fallback
4. **STT failover**: Deepgram primary -> Google STT fallback
5. **Total system failure**: Forward to physical answering service or voicemail

### Monitoring and Alerts

| Metric | Threshold | Action |
|--------|-----------|--------|
| Response latency | > 2s average | Alert + investigate |
| Call drop rate | > 2% | Alert + check telephony |
| STT accuracy | < 90% | Switch to backup engine |
| LLM error rate | > 5% | Switch to fallback model |
| CRM lookup timeout | > 3s | Use filler + retry |
| Concurrent calls | > 80% capacity | Alert for scaling |

---

## Cost Implications

### Monthly Infrastructure Costs

| Component | Low Volume (500 min) | Medium (2,000 min) | High (5,000 min) |
|-----------|---------------------|---------------------|-------------------|
| Vapi platform | $25 | $100 | $250 |
| LLM (GPT-4o-mini primary) | $15-25 | $60-100 | $150-250 |
| Deepgram STT | $2.15 | $8.60 | $21.50 |
| ElevenLabs TTS | $15-30 | $60-120 | $150-300 |
| Twilio telephony | $4-7 | $16-28 | $40-70 |
| Phone number | $2 | $2 | $2 |
| n8n/Make (workflows) | $20 | $20 | $50 |
| **Monthly total** | **$83-109** | **$267-379** | **$664-943** |

### Cost Optimization Levers
- Use OpenAI TTS instead of ElevenLabs for non-critical responses (60-80% TTS cost savings)
- Use prompt caching to reduce LLM costs by up to 80% on repeated queries
- Negotiate Vapi enterprise pricing at 5,000+ min/month
- Use Deepgram for both STT and TTS (bundled pricing available)

---

## Estimated Build Hours

| Phase | Hours | Description |
|-------|-------|-------------|
| Architecture finalization + platform setup | 6-8h | Vapi account, Twilio provisioning, base config |
| Greeting Agent development | 4-6h | Prompt engineering, intent classification testing |
| Deal Qualification Agent | 8-12h | CRM integration, qualifying logic, routing rules |
| Client Lookup Agent | 4-6h | Nutshell API integration, phone/name search |
| Department Router | 6-8h | Employee directory, availability checks, transfer logic |
| Knowledge Base Agent | 6-8h | Document prep, RAG config, accuracy testing |
| Scheduling Agent | 6-8h | Google Calendar integration, booking flow |
| After-Hours Agent | 4-6h | Message taking, emergency escalation, booking fallback |
| Latency optimization | 4-6h | Engine selection, streaming config, caching |
| Integration testing | 8-12h | End-to-end call flows, edge cases |
| UAT with Steven + team | 4-6h | Real-world testing, prompt refinement |
| **Total** | **60-86h** | ~3-4 weeks with dedicated developer |

---

## Sources

- [Vapi Squads Documentation](https://docs.vapi.ai/squads)
- [Vapi Handoff Tool](https://docs.vapi.ai/squads/handoff)
- [Vapi Squads Example](https://docs.vapi.ai/squads-example)
- [Retell AI Architecture](https://www.retellai.com/blog/inside-retell-ai-conversational-ai-phone-system)
- [Voice AI Latency Optimization](https://www.ruh.ai/blogs/voice-ai-latency-optimization)
- [STT/TTS Pipeline Architecture](https://softcery.com/lab/ai-voice-agents-real-time-vs-turn-based-tts-stt-architecture)
- [Deepgram Voice AI Workflows](https://deepgram.com/learn/designing-voice-ai-workflows-using-stt-nlp-tts)
- [Twilio Core Latency Guide](https://www.twilio.com/en-us/blog/developers/best-practices/guide-core-latency-ai-voice-agents)

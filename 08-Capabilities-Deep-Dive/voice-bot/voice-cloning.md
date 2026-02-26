# Voice Cloning Platform Comparison: ElevenLabs vs PlayHT vs Resemble AI

## Overview

Voice cloning enables SW Recovery Services to deploy an AI voice bot that sounds like Steven, creating a consistent brand experience across all inbound calls. The cloned voice would greet callers with a natural, recognizable voice before routing based on deal size. This document compares three leading platforms for voice model training, quality, latency, compliance, and pricing.

**Key requirement**: Steven must record 30+ minutes of high-quality audio to train a professional-grade voice clone. The clone must integrate with the voice bot platform (Bland AI, Vapi, or Retell) and meet FTC/FCC disclosure requirements for AI-generated voice calls.

---

## Platform Comparison

### ElevenLabs

**Training Process**
- Instant Voice Cloning: 10-60 seconds of sample audio (lower quality, good for testing)
- Professional Voice Cloning: 30+ minutes of studio-quality recordings required
- Professional clones produce nearly indistinguishable results from the original voice
- Supports 32+ languages automatically from a single English training set
- Training typically completes within hours for professional clones

**Voice Quality**
- Rated highest quality in blind tests (37% top score vs 11% for PlayHT)
- Best emotional range and naturalness among all platforms
- Flash model optimized for real-time conversational use cases
- Turbo v2.5 model available for ultra-low latency applications

**API & Integration**
- RESTful API with WebSocket streaming support
- Voice referenced by unique voice_id in all API calls
- Streaming endpoints for real-time TTS with chunked audio output
- Output formats: MP3, PCM (44.1kHz on Scale+), OGG
- SDKs available for Python, Node.js, and other languages

**Latency**
- Flash model: sub-500ms first-byte latency
- Turbo v2.5: ~300ms first-byte latency
- Suitable for real-time voice bot conversations

**Pricing (2025-2026)**
| Plan | Monthly Cost | Credits/Month | Voice Clones | Notes |
|------|-------------|---------------|--------------|-------|
| Free | $0 | 10k chars | 1 instant | Non-commercial |
| Starter | $5/month | 30k chars | 3 instant | Commercial license |
| Creator | $22/month | 100k chars | 10 instant | API access |
| Pro | $99/month | 500k chars | 20 instant + 1 professional | Priority support |
| Scale | $330/month | 2M chars | 20 instant + 3 professional | 44.1kHz PCM, API priority |
| Business | $1,320/month | 11M chars | 20 instant + 3 professional | Low-latency TTS ~5c/min |
| Enterprise | Custom | Custom | Custom | SSO, HIPAA, SLAs |

**Recommended tier for OpenClaw**: Scale ($330/month) or Business ($1,320/month) for professional voice clone + low-latency API access.

---

### PlayHT

**Training Process**
- Voice cloning requires only 30 seconds of sample audio
- Lower barrier to entry but reduced fidelity compared to longer training sets
- PlayHT 2.0 and 3.0 models for improved quality
- 600+ pre-built voices across 142 languages available

**Voice Quality**
- Good for content creation and voiceovers
- Lower quality than ElevenLabs in blind comparison tests
- PlayHT 3.0 Mini model improved conversational quality
- Better suited for pre-recorded content than real-time conversations

**API & Integration**
- RESTful API with streaming support
- WebSocket-based real-time streaming
- Clone voices referenced by voice ID
- Output formats: MP3, WAV, OGG, FLAC, MULAW
- SDKs for Python and Node.js

**Latency**
- PlayHT 2.0: ~800ms first-byte latency (improved from earlier versions)
- PlayHT 3.0 Mini: ~190ms+ latency (better but still higher than ElevenLabs)
- Adequate for some conversational use cases, but noticeable delay in rapid exchanges

**Pricing (2025-2026)**
| Plan | Monthly Cost | Characters | Voice Clones | Notes |
|------|-------------|-----------|--------------|-------|
| Free | $0 | Limited | 1 | Non-commercial |
| Creator | $31.20/month (annual) | 3M chars/year | Multiple | Content creation |
| Pro | $49/month (promo) | Unlimited | HQ clones | Regular $99/month |
| Enterprise | Custom | Unlimited | Unlimited HQ | SOC2, SSO, dedicated AM |

---

### Resemble AI

**Training Process**
- Rapid Voice Cloning: 5 minutes of audio for basic clone
- Professional Voice Cloning: 25-30+ minutes recommended for production quality
- Supports 23 languages
- Real-time speech-to-speech capabilities

**Voice Quality**
- Strong enterprise-grade quality with fine-tuning options
- Real-time voice conversion (speech-to-speech) unique feature
- Deepfake detection built into the platform (Resemble Detect)
- Good emotional control and SSML support

**API & Integration**
- RESTful API with real-time streaming
- On-premise deployment option (air-gapped, no cloud dependency)
- Fully self-hosted inference available behind customer firewall
- Integrates with telephony platforms via API
- Custom model fine-tuning available for enterprise

**Latency**
- Cloud API: competitive real-time latency
- On-premise: depends on hardware, can achieve sub-200ms
- Speech-to-speech mode for ultra-low latency voice conversion

**Pricing (2025-2026)**
| Plan | Monthly Cost | Included | Voice Clones | Notes |
|------|-------------|---------|--------------|-------|
| Pay-as-you-go | $0.006/sec ($0.36/min) | Per usage | Varies | No commitment |
| Creator | $19/month | Basic | 5 rapid + 1 professional | |
| Professional | $99/month | 10k seconds (~2.78 hrs) | 5 rapid + 1 professional | |
| Scale | $299/month | Higher volume | More clones | |
| Business | $699/month | High volume | Multiple professional | |
| Enterprise | Custom | Custom | Unlimited | On-premise, SSO, SLAs |

---

## FTC/FCC Compliance Requirements

### Regulatory Framework (2025-2026)

**FCC Declaratory Ruling (Feb 2024)**
- AI-generated voices are classified as "artificial or prerecorded voice" under the TCPA
- All TCPA consent requirements apply to AI voice calls
- Prior express consent required from called party
- Applies to both outbound and certain inbound scenarios

**FTC Telemarketing Sales Rule Updates (2024-2025)**
- Voice cloning technology falls under existing robocall prohibitions
- AI-generated voices cannot be used to impersonate or deceive
- Opt-out processing must occur within 10 business days (as of April 2025)

**Key Compliance Requirements for SW Recovery**
1. **Disclosure**: Must disclose within first 30 seconds that the caller is speaking with an AI assistant (some states require immediate disclosure)
2. **Consent**: Prior express consent required for outbound calls; inbound calls have lighter requirements since the caller initiates
3. **Identification**: Must identify the business name and provide callback number
4. **Opt-out**: Must offer clear opt-out mechanism and honor requests within 10 business days
5. **Recording consent**: Separate from AI disclosure; varies by state (one-party vs two-party)

**Recommended disclosure script for Steven's bot**:
> "Thank you for calling SW Recovery Services. You're speaking with my AI assistant, which uses Steven's voice to help route your call. How can I help you today?"

**Penalties for Non-Compliance**
- TCPA violations: $500-$1,500 per call
- FTC Telemarketing Sales Rule violations: up to $51,744 per call
- State-level penalties vary (e.g., Texas explicitly prohibits undisclosed voice cloning)

### Inbound Call Advantage
Since SW Recovery's bot is **inbound only**, the compliance burden is lighter:
- Caller initiates the contact (implied consent to interact)
- Still must disclose AI nature of the conversation
- No cold-calling consent issues
- Primary risk is failing to disclose AI nature, not consent violations

---

## Voice Bot Platform Integration

### Integration Architecture

```
Caller --> Telephony (Twilio/Vonage) --> Voice Bot (Bland/Vapi/Retell)
                                              |
                                              v
                                    Voice Clone API (ElevenLabs)
                                              |
                                              v
                                    Cloned Voice Audio Stream
                                              |
                                              v
                                    Caller hears Steven's voice
```

### Integration Points by Voice Bot Platform

| Voice Bot | ElevenLabs | PlayHT | Resemble AI |
|-----------|-----------|--------|-------------|
| Bland AI | Native integration, voice_id config | API integration | API integration |
| Vapi | Native ElevenLabs provider | PlayHT provider supported | Custom API integration |
| Retell | Built-in ElevenLabs support | API bridge needed | API bridge needed |

**ElevenLabs has the strongest native integration** with all three voice bot platforms, reducing implementation complexity.

### Latency Budget for Voice Bot

Total acceptable latency for natural conversation: ~1,500ms round-trip

| Component | Budget | Notes |
|-----------|--------|-------|
| Speech-to-text | 200-400ms | Deepgram/Whisper |
| LLM processing | 300-600ms | GPT-4o-mini or Claude Haiku |
| Text-to-speech (clone) | 200-500ms | ElevenLabs Flash/Turbo |
| Network overhead | 100-200ms | Varies by provider |
| **Total** | **800-1,700ms** | Target under 1,500ms |

---

## Recommendation

### Primary Choice: ElevenLabs (Scale or Business Plan)

**Rationale**:
1. **Highest voice quality** in independent testing (37% top rating)
2. **Best native integration** with Bland AI, Vapi, and Retell
3. **Lowest latency** with Flash/Turbo models (~300-500ms)
4. **Professional Voice Cloning** with 30+ min training produces near-identical results
5. **32+ language support** from single English training set (future expansion)
6. **Strong compliance tooling** with content moderation and safety features

**Secondary Choice: Resemble AI** if on-premise deployment or speech-to-speech conversion becomes a requirement.

### Training Process for Steven

1. **Equipment**: Studio-quality microphone (e.g., Shure SM7B or equivalent), quiet room
2. **Script preparation**: Prepare 30-45 minutes of diverse reading material covering various tones, speeds, and emotional registers relevant to business calls
3. **Recording guidelines**:
   - 44.1kHz or higher sample rate, WAV format
   - Minimal background noise
   - Consistent microphone distance (6-8 inches)
   - Include greetings, questions, explanations, and natural pauses
4. **Upload and training**: Upload via ElevenLabs Professional Voice Cloning interface
5. **Quality validation**: Test clone against real voice in A/B comparison
6. **Deployment**: Configure voice_id in voice bot platform

---

## Cost Implications

### Monthly Operating Costs

| Component | Cost | Notes |
|-----------|------|-------|
| ElevenLabs Scale plan | $330/month | 2M characters, 3 professional clones |
| Overage (if needed) | $0.18/1k chars | Beyond plan allocation |
| Voice bot platform | Included in bot costs | Bland/Vapi/Retell pricing separate |
| **Total voice cloning** | **$330-$500/month** | Depending on call volume |

### One-Time Costs

| Item | Cost | Notes |
|------|------|-------|
| Recording equipment (if needed) | $300-$500 | Microphone, pop filter, interface |
| Studio time (alternative) | $200-$400 | Professional recording studio |
| Integration development | 8-12 hours | API setup and testing |

---

## Estimated Build Hours

| Task | Hours | Notes |
|------|-------|-------|
| Recording session planning & script prep | 3 | Diverse content for training |
| Recording session with Steven | 2-3 | 30-45 min of clean audio |
| Audio cleanup and formatting | 2 | Noise removal, segmentation |
| ElevenLabs account setup and clone training | 2 | Upload, train, validate |
| Voice bot integration (API config) | 4-6 | Connect clone to Bland/Vapi/Retell |
| FTC compliance review and disclosure setup | 2-3 | Legal review, script finalization |
| Testing and quality assurance | 4-6 | A/B testing, latency validation |
| **Total** | **19-25 hours** | |

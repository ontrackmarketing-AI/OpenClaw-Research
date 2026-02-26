# Plaud Developer Platform: API & Webhook Integration

## Overview

Plaud's Developer Platform (launched October 2025) provides full-stack APIs and SDKs for capturing,
transcribing, and extracting intelligence from in-person conversations. Steven uses Plaud NotePin
for voice memos and meeting recordings. This document covers how to automatically push transcripts,
summaries, and action items from Plaud into our knowledge base and CRM pipeline.

**Target Flow:**
```
Meeting recorded (Plaud NotePin/Note)
  -> Plaud cloud transcribes (112 languages, speaker diarization)
  -> Webhook fires: audio_transcribe.completed
  -> n8n receives payload (transcript + summary + action items)
  -> Store in Supabase knowledge base
  -> Update Nutshell CRM (contact notes, activity log)
  -> Trigger downstream workflows (blog content, follow-up tasks)
```

**Key Devices:**
| Device | Use Case | Price |
|--------|----------|-------|
| NotePin | Wearable (30g), hands-free recording, interviews | ~$169 |
| Note | Daily voice memos, meeting notes | ~$159 |
| Note Pro | Professional — board meetings, legal depositions | ~$249 |

---

## API/Integration Details

### Authentication

Plaud uses token-based OAuth authentication:

```
POST /auth/token
Content-Type: application/json

{
  "client_id": "your_client_id",
  "secret_key": "your_secret_key"
}
```

Returns an API token for subsequent requests. Tokens should be stored securely and refreshed
before expiration.

### Core API Endpoints

#### Device Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/devices/{id}` | GET | Get device by ID (returns device model or 404) |
| `/devices/bind` | POST | Bind device to user (requires `sn_type`, `sn`) |
| `/devices/unbind` | POST | Unbind device from user account |

#### File Operations
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/files/presigned-urls` | POST | Generate presigned URLs for multipart upload |
| `/files/complete-upload` | POST | Finalize upload (`file_id`, `upload_id`, `part_list`) |

#### Workflow Management (Transcription + AI)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/workflows/submit` | POST | Submit a workflow (list of tasks: transcribe, summarize, etc.) |
| `/workflows/{id}/status` | GET | Get workflow execution status |
| `/workflows/{id}/result` | GET | Get workflow result including all task outputs |

#### AI Capabilities
- **Transcription**: Audio-to-text, 112 languages, speaker diarization, custom vocabulary
- **AI Summary**: Multi-dimensional summaries (key points, action items, decisions)
- **Live Transcription**: Real-time via WebSocket connection

### Webhook Configuration

#### Setup Steps
1. Navigate to Plaud Developer Portal > Event Subscriptions
2. Click "Add Subscription"
3. Configure:
   - **Name**: Descriptive identifier (e.g., "OpenClaw Knowledge Base Push")
   - **Callback URL**: Your HTTPS endpoint (e.g., `https://n8n.openclaw.com/webhook/plaud`)
   - **Events**: Select `audio_transcribe.completed` and other desired events

#### Webhook Event Types
| Event | Description |
|-------|-------------|
| `audio_transcribe.completed` | Transcription finished — transcript + metadata ready |
| `device.connectivity_changed` | Device connected/disconnected status update |

*Note: Plaud's documentation indicates additional event types exist. Check the
full documentation index for the complete list.*

#### Webhook Payload Structure

```json
{
  "event_type": "audio_transcribe.completed",
  "data": {
    "file_id": "abc123-def456",
    "transcript": {
      "text": "Full transcript text...",
      "segments": [
        {
          "speaker": "Speaker 1",
          "start_time": 0.0,
          "end_time": 12.5,
          "text": "Segment text..."
        }
      ],
      "language": "en",
      "duration_seconds": 1845
    },
    "summary": {
      "key_points": ["..."],
      "action_items": ["..."],
      "decisions": ["..."]
    },
    "metadata": {
      "device_type": "notepin",
      "recording_mode": "conversation",
      "created_at": "2026-01-15T14:30:00Z"
    }
  }
}
```

*Note: Exact payload schema may vary. The above is based on documented fields and
platform descriptions. Verify against actual webhook deliveries during development.*

#### Signature Verification (HMAC-SHA256)

Plaud signs every webhook with the `Plaud-Signature` header. Always verify:

```python
import hmac
import hashlib

def verify_plaud_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

```python
# Flask example
from flask import Flask, request, abort

app = Flask(__name__)
WEBHOOK_SECRET = os.environ['PLAUD_WEBHOOK_SECRET']

@app.route('/webhook/plaud', methods=['POST'])
def handle_plaud_webhook():
    signature = request.headers.get('Plaud-Signature', '')
    if not verify_plaud_signature(request.data, signature, WEBHOOK_SECRET):
        abort(401)

    event = request.json
    if event['event_type'] == 'audio_transcribe.completed':
        process_transcript(event['data'])

    return '', 200
```

#### Idempotency
Plaud may deliver the same event more than once. Implement idempotency:
- Track processed `file_id` values in a set/database
- Skip duplicates silently (return 200 to prevent retries)

### SDK Options
| Platform | SDK | Use Case |
|----------|-----|----------|
| Android | Android SDK | Mobile companion app for device Bluetooth transfer |
| iOS | iOS SDK | Mobile companion app for device Bluetooth transfer |
| Server | REST API + WebSocket | Cloud processing, webhook reception |

**Important**: Plaud devices transfer files to cloud via a mobile app over Bluetooth.
The mobile SDK is required for the device-to-cloud file transfer step. Once files
reach Plaud cloud, the REST API and webhooks handle everything server-side.

---

## Implementation Approach

### Phase 1: Webhook Receiver (Week 1)
1. Create n8n webhook node at `/webhook/plaud`
2. Implement signature verification in n8n Code node
3. Parse incoming `audio_transcribe.completed` events
4. Store raw transcript + summary in Supabase `knowledge_base` table
5. Log metadata (device, duration, language, timestamp)

### Phase 2: CRM Integration (Week 2)
1. Extract speaker names from diarized transcript
2. Match speakers to Nutshell contacts (fuzzy name matching)
3. Create Nutshell activity/note with meeting summary
4. Attach action items as Nutshell tasks
5. Tag contacts with "meeting-recorded" for tracking

### Phase 3: Knowledge Base Enrichment (Week 3)
1. Chunk transcripts for vector embedding (Supabase pgvector)
2. Generate embeddings via OpenAI text-embedding-3-small
3. Enable semantic search across all recorded conversations
4. Feed transcript insights into AI voice bot knowledge base
5. Auto-generate blog content drafts from meeting transcripts

### Architecture Diagram
```
Plaud NotePin
    |
    | (Bluetooth)
    v
Plaud Mobile App
    |
    | (WiFi/LTE)
    v
Plaud Cloud (transcribe + summarize)
    |
    | (webhook POST)
    v
n8n Webhook Node
    |
    +---> Supabase: knowledge_base table (raw storage)
    +---> Supabase: pgvector embeddings (semantic search)
    +---> Nutshell CRM: contact notes + activity log
    +---> Content Pipeline: blog draft trigger
```

### Error Handling
- **Webhook failures**: n8n retries with exponential backoff
- **Duplicate events**: Idempotency check on `file_id`
- **Missing speakers**: Flag for manual review in Nutshell
- **Transcription quality**: Confidence thresholds (reject < 0.7)

---

## Cost Implications

### Plaud Platform Costs
| Item | Cost | Notes |
|------|------|-------|
| Plaud NotePin hardware | ~$169 one-time | Steven already owns device |
| Plaud subscription | $7.99-$19.99/mo | Depends on plan tier (Basic/Pro/Ultra) |
| Developer Platform access | TBD | Contact Plaud sales for enterprise API pricing |

### Infrastructure Costs (Our Side)
| Item | Cost | Notes |
|------|------|-------|
| n8n webhook processing | $0 | Self-hosted on Mac Mini |
| Supabase storage | ~$0.02/GB/mo | Transcripts are small text files |
| OpenAI embeddings | ~$0.02/1M tokens | For vector search indexing |
| Nutshell API calls | $0 | Included in CRM subscription |

### Estimated Monthly Cost
- ~20-40 recordings/month at current volume
- Transcript storage: negligible (~$0.01/mo)
- Embeddings: ~$0.50/mo
- **Total incremental cost: ~$1-5/mo** (excluding Plaud subscription)

---

## Estimated Build Hours

| Phase | Tasks | Hours |
|-------|-------|-------|
| Phase 1: Webhook Receiver | n8n webhook, signature verify, Supabase storage | 6-8 |
| Phase 2: CRM Integration | Speaker matching, Nutshell notes, task creation | 8-10 |
| Phase 3: Knowledge Base | Vector embeddings, semantic search, content triggers | 10-12 |
| Testing & QA | End-to-end testing, error scenarios, monitoring | 4-6 |
| **Total** | | **28-36 hours** |

### Dependencies
- Plaud Developer Platform API access (apply at developer portal)
- Plaud subscription with webhook support
- n8n instance with webhook capability
- Supabase project with pgvector extension
- Nutshell CRM API credentials

### Risks
- Plaud Developer Platform is new (Oct 2025) — documentation may be incomplete
- Webhook event types beyond `audio_transcribe.completed` are not fully documented
- Mobile app required for device-to-cloud transfer (no direct device API)
- API rate limits and pricing not fully published yet

---

## Compliance & Security

Plaud Developer Platform certifications:
- **SOC 2 Type II** — Security controls audited
- **HIPAA** — Healthcare data handling compliant
- **GDPR** — EU data protection compliant
- **ISO 27001/27701** — Information security management
- **EN18031** — Cybersecurity for radio equipment

All webhook communications require HTTPS. End-to-end encryption between devices
and platform. Signature verification (HMAC-SHA256) on all webhook payloads.

---

## References

- [Plaud Developer Platform](https://www.plaud.ai/pages/developer-platform)
- [Plaud API Documentation](https://docs.plaud.ai)
- [Plaud Webhook Events](https://docs.plaud.ai/documentation/developer_guides/webhook_events)
- [Plaud Device Operations](https://docs.plaud.ai/documentation/capabilities/device_operations)
- [Plaud Developer Platform Launch (PR Newswire)](https://www.prnewswire.com/news-releases/plaud-launches-developer-platform-to-unlock-the-missing-half-of-conversational-intelligence-in-person-interactions-302576832.html)
- [Plaud Zapier Integration](https://zapier.com/apps/plaud/integrations)

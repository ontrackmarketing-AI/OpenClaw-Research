# CallRail Integration: Call Recording Export & Transcript Extraction

## Overview

CallRail is Steven's call tracking platform that captures every inbound and outbound call
with recordings and (with Conversational Intelligence) full transcriptions. These call
recordings and transcripts are a rich, untapped knowledge base — they contain how Steven
handles objections, explains services, negotiates with debtors, and coaches his team.

This document covers extracting CallRail data via API and webhooks to feed the AI voice bot's
knowledge base, enrich CRM contact records, and surface call insights for training and
content creation.

**Data Flow:**
```
Phone Call (inbound/outbound via CallRail)
    |
    v
CallRail Platform
    - Records call (MP3)
    - Transcribes conversation (if Conversational Intelligence plan)
    - Scores call (auto + manual)
    - Tags and categorizes
    |
    +---> [Webhook: post_call / call_modified]
    |         |
    |         v
    |     n8n Automation
    |         |
    |         +---> Supabase: Knowledge base (transcripts)
    |         +---> Nutshell CRM: Contact activity log
    |         +---> AI Voice Bot: Training data
    |
    +---> [API: Bulk historical export]
              |
              v
          n8n Batch Workflow
              |
              +---> Supabase: Historical transcript archive
              +---> Vector embeddings for semantic search
```

**Key Objectives:**
1. Real-time capture of new call transcripts via webhooks
2. Bulk export of historical call recordings and transcripts (25-month retention)
3. Feed transcripts into AI voice bot knowledge base
4. Link call data to Nutshell CRM contacts
5. Surface insights for blog content and training materials

---

## API/Integration Details

### Authentication

CallRail uses token-based authentication via HTTP header:

```bash
Authorization: Token token="YOUR_API_KEY"
```

**Getting an API Key:**
1. Log in to CallRail dashboard
2. Navigate to Settings > API > API Keys
3. Generate a new API key
4. Keys are user-scoped (access matches the user's permissions)
5. Keys do not expire but can be revoked

### Base URL

```
https://api.callrail.com/v3/
```

All endpoints are prefixed with `/v3/a/{account_id}/` where `account_id` is your
CallRail account identifier.

### Core Endpoints

#### 1. List Accounts
```
GET /v3/a.json
```
Returns all accounts accessible to the API key holder. Use to retrieve your `account_id`.

#### 2. List Calls (with Transcripts)
```
GET /v3/a/{account_id}/calls.json
```

**Key Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `fields` | string | Comma-separated additional fields (e.g., `transcription,recording,call_summary`) |
| `date_range` | string | Predefined ranges: `today`, `yesterday`, `last_7_days`, `last_30_days`, `this_month`, `last_month`, `all_time` |
| `start_date` | string | Custom start date (ISO 8601) |
| `end_date` | string | Custom end date (ISO 8601) |
| `call_type` | string | `first_call`, `missed`, `voicemails`, `inbound`, `outbound` |
| `answer_status` | string | `answered`, `missed`, `voicemail` |
| `lead_status` | string | `good_lead`, `not_a_lead`, `not_scored` |
| `tags` | string | Filter by tag name(s) |
| `search` | string | Search across customer name, number, note, source |
| `per_page` | integer | Results per page (default 100, max 250) |
| `page` | integer | Page number for offset pagination |
| `sort` | string | Sort field (e.g., `start_time`, `duration`, `customer_name`) |
| `order` | string | `asc` or `desc` |

**Example Request (with transcription):**
```bash
curl -H "Authorization: Token token=\"YOUR_API_KEY\"" \
  "https://api.callrail.com/v3/a/ACCOUNT_ID/calls.json?fields=transcription,recording,call_summary,keywords_spotted&date_range=last_30_days&per_page=100"
```

**Response Structure:**
```json
{
  "page": 1,
  "per_page": 100,
  "total_pages": 5,
  "total_records": 487,
  "calls": [
    {
      "id": "CAL8154748ae6bd4e278a7a",
      "company_id": "COM8154748ae6bd4e278",
      "company_name": "SW Recovery Services",
      "start_time": "2026-01-15T14:30:00.000-07:00",
      "duration": 245,
      "direction": "inbound",
      "answered": true,
      "customer_name": "John Smith",
      "customer_phone_number": "+15551234567",
      "customer_city": "Phoenix",
      "customer_state": "AZ",
      "tracking_phone_number": "+18005551234",
      "source": "Google Ads",
      "medium": "paid",
      "campaign": "debt_recovery_2026",
      "landing_page_url": "https://swrecovery.com/services",
      "lead_status": "good_lead",
      "tags": ["new_client", "high_value"],
      "note": "Interested in commercial debt recovery",
      "value": "$5,000.00",
      "recording": "https://api.callrail.com/v3/a/ACCOUNT_ID/calls/CAL.../recording.json",
      "recording_duration": "4:05",
      "recording_player": "https://app.callrail.com/calls/CAL.../recording",
      "transcription": "Agent: Thank you for calling SW Recovery Services, this is Steven. How can I help you today?\nCaller: Hi Steven, I have some outstanding invoices that...",
      "call_summary": "Caller inquired about commercial debt recovery services for outstanding invoices totaling approximately $50,000. Steven explained the contingency fee structure and timeline expectations.",
      "keywords_spotted": [
        {
          "keyword": "debt recovery",
          "speaker": "caller",
          "timestamp": "0:45"
        }
      ]
    }
  ]
}
```

#### 3. Get Single Call
```
GET /v3/a/{account_id}/calls/{call_id}.json
```
Returns full details for a specific call. Same field options as list endpoint.

#### 4. Get Call Recording (MP3)
```
GET /v3/a/{account_id}/calls/{call_id}/recording.json
```
Returns a URL to the MP3 recording file. The URL is temporary but does not expire
within 24 hours. Download and store recordings in your own storage for long-term access.

#### 5. Update Call (Add Notes/Tags)
```
PUT /v3/a/{account_id}/calls/{call_id}.json
```

**Updateable Fields:**
```json
{
  "note": "Follow up next Tuesday",
  "tags": ["follow_up", "high_priority"],
  "lead_status": "good_lead",
  "value": "$10,000",
  "customer_name": "John Smith",
  "spam": false
}
```

#### 6. Call Summary/Timeseries
```
GET /v3/a/{account_id}/calls/summary.json
GET /v3/a/{account_id}/calls/timeseries.json
```
Aggregated call statistics for dashboards and reporting.

### Webhook Configuration

#### Setup
1. CallRail Dashboard > Settings > Webhooks
2. Add webhook URL (e.g., `https://n8n.openclaw.com/webhook/callrail`)
3. Select events to subscribe to
4. Set authentication (secret token for payload validation)

#### Webhook Event Types

| Event | Trigger | Timing | Key Data |
|-------|---------|--------|----------|
| `pre_call` | Before call connects | Immediate | Caller info, tracking number, source |
| `post_call` | After call ends | Up to 20 min delay | Recording URL, duration, basic transcript |
| `call_modified` | Call data updated | After manual/auto scoring | Full transcript, tags, notes, score, value |
| `outbound_post_call` | Outbound call ends | Up to 20 min delay | Recording, duration |
| `outbound_call_modified` | Outbound call updated | After scoring | Full transcript, tags, notes |
| `text_message_received` | Inbound SMS | Immediate | Message content, customer info |
| `text_message_sent` | Outbound SMS | Immediate | Message content |
| `form_submission` | Form submitted | Immediate | Form fields, source |

**Recommended Webhook Strategy:**
- Subscribe to `call_modified` (not `post_call`) for transcript access
- `call_modified` fires after transcription is complete and includes all enriched data
- `post_call` may fire before transcript is ready

#### Webhook Payload (call_modified)

```json
{
  "callrail_company_id": "COM8154748...",
  "type": "call_modified",
  "data": {
    "id": "CAL8154748...",
    "answered": true,
    "direction": "inbound",
    "duration": 245,
    "start_time": "2026-01-15T14:30:00.000-07:00",
    "customer_name": "John Smith",
    "customer_phone_number": "+15551234567",
    "tracking_phone_number": "+18005551234",
    "source": "Google Ads",
    "recording": "https://api.callrail.com/v3/.../recording.json",
    "recording_duration": "4:05",
    "transcription_text": "Agent: Thank you for calling...",
    "tags": ["new_client"],
    "note": "Interested in commercial recovery",
    "value": "$5,000.00",
    "lead_status": "good_lead",
    "auto_score": 85,
    "manual_score": null
  }
}
```

#### Webhook Signature Verification

CallRail provides a secret token for webhook validation. Verify the signature
on incoming requests:

```python
import hmac
import hashlib

def verify_callrail_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### Rate Limits

| Category | Per Hour | Per Day |
|----------|---------|---------|
| General API | 1,000 | 10,000 |
| SMS Send | 150 | 1,000 |
| Outbound Call | 100 | 2,000 |

Exceeding limits returns HTTP 429. Contact CallRail support for limit increases.

### Data Retention

CallRail retains communication records for **25 months**. API requests for data
outside this window will return errors. Plan bulk export accordingly.

---

## Implementation Approach

### Phase 1: Real-Time Webhook Integration (Week 1-2)

**n8n Workflow: New Call -> Knowledge Base**

```
[Webhook Trigger: CallRail call_modified]
    |
    v
[Code Node: Validate webhook signature]
    |
    v
[IF Node: Has transcription_text?]
    |-- NO  --> [End: Skip non-transcribed calls]
    |
    |-- YES --> [Code Node: Extract transcript + metadata]
                    |
                    v
                [HTTP Request: Store in Supabase knowledge_base]
                    |
                    v
                [Code Node: Generate vector embedding]
                    |
                    v
                [HTTP Request: Store embedding in document_embeddings]
                    |
                    v
                [IF Node: Customer exists in Nutshell?]
                    |-- YES --> [HTTP Request: Add call note to Nutshell contact]
                    |-- NO  --> [HTTP Request: Create new Nutshell contact + note]
```

**Supabase Schema for Call Transcripts:**
```sql
CREATE TABLE call_transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    callrail_call_id TEXT UNIQUE NOT NULL,
    direction TEXT,                      -- inbound, outbound
    duration_seconds INTEGER,
    customer_name TEXT,
    customer_phone TEXT,
    source TEXT,                          -- Google Ads, organic, direct, etc.
    transcript_text TEXT NOT NULL,
    call_summary TEXT,
    tags TEXT[],
    lead_status TEXT,
    auto_score INTEGER,
    recording_url TEXT,
    recording_downloaded BOOLEAN DEFAULT FALSE,
    nutshell_contact_id INTEGER,
    keywords_spotted JSONB DEFAULT '[]',
    call_date TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for full-text search
CREATE INDEX idx_call_transcripts_fts ON call_transcripts
    USING GIN (to_tsvector('english', transcript_text));
```

### Phase 2: Historical Bulk Export (Week 2-3)

Export all existing call recordings and transcripts from the past 25 months
to build the initial knowledge base.

**Bulk Export Script:**
```python
import requests
import time
from datetime import datetime, timedelta

CALLRAIL_API_KEY = "YOUR_API_KEY"
ACCOUNT_ID = "YOUR_ACCOUNT_ID"
BASE_URL = f"https://api.callrail.com/v3/a/{ACCOUNT_ID}"
HEADERS = {"Authorization": f'Token token="{CALLRAIL_API_KEY}"'}


def export_all_calls():
    """Export all calls with transcripts from the past 25 months."""
    # CallRail retains 25 months of data
    start_date = (datetime.utcnow() - timedelta(days=750)).isoformat()
    end_date = datetime.utcnow().isoformat()

    page = 1
    total_exported = 0

    while True:
        params = {
            'fields': 'transcription,recording,call_summary,keywords_spotted',
            'start_date': start_date,
            'end_date': end_date,
            'per_page': 250,  # Max per page
            'page': page,
            'sort': 'start_time',
            'order': 'asc'
        }

        response = requests.get(
            f"{BASE_URL}/calls.json",
            headers=HEADERS,
            params=params
        )

        if response.status_code == 429:
            # Rate limited - wait and retry
            print("Rate limited, waiting 60 seconds...")
            time.sleep(60)
            continue

        data = response.json()
        calls = data.get('calls', [])

        if not calls:
            break

        for call in calls:
            store_call_transcript(call)
            total_exported += 1

        print(f"Page {page}/{data['total_pages']} - "
              f"Exported {total_exported}/{data['total_records']}")

        if page >= data['total_pages']:
            break

        page += 1
        time.sleep(1)  # Respect rate limits (1 req/sec = 3600/hr, well under 1000/hr)

    print(f"Export complete: {total_exported} calls exported")


def store_call_transcript(call: dict):
    """Store a single call transcript in Supabase."""
    # Only store calls with transcripts
    transcript = call.get('transcription', '')
    if not transcript:
        return

    supabase.table('call_transcripts').upsert({
        'callrail_call_id': call['id'],
        'direction': call.get('direction', 'unknown'),
        'duration_seconds': call.get('duration', 0),
        'customer_name': call.get('customer_name', ''),
        'customer_phone': call.get('customer_phone_number', ''),
        'source': call.get('source', ''),
        'transcript_text': transcript,
        'call_summary': call.get('call_summary', ''),
        'tags': call.get('tags', []),
        'lead_status': call.get('lead_status', ''),
        'auto_score': call.get('auto_score'),
        'recording_url': call.get('recording', ''),
        'call_date': call.get('start_time'),
    }, on_conflict='callrail_call_id').execute()
```

### Phase 3: Recording Download & Archive (Week 3-4)

```python
def download_recordings():
    """Download MP3 recordings for long-term storage."""
    # Get calls with recordings that haven't been downloaded
    calls = supabase.table('call_transcripts').select('*').eq(
        'recording_downloaded', False
    ).not_.is_('recording_url', 'null').execute()

    for call in calls.data:
        try:
            # Get recording URL from CallRail
            rec_response = requests.get(
                call['recording_url'],
                headers=HEADERS
            )

            if rec_response.status_code == 200:
                rec_data = rec_response.json()
                mp3_url = rec_data.get('url')

                if mp3_url:
                    # Download MP3
                    mp3_response = requests.get(mp3_url)
                    filename = f"call_{call['callrail_call_id']}.mp3"

                    # Upload to Supabase Storage
                    supabase.storage.from_('call-recordings').upload(
                        filename, mp3_response.content,
                        {'content-type': 'audio/mpeg'}
                    )

                    # Mark as downloaded
                    supabase.table('call_transcripts').update(
                        {'recording_downloaded': True}
                    ).eq('id', call['id']).execute()

            time.sleep(1)  # Rate limiting

        except Exception as e:
            print(f"Error downloading {call['callrail_call_id']}: {e}")
```

### Phase 4: Knowledge Base Enrichment (Week 4)

1. **Vector Embeddings**: Chunk transcripts and generate embeddings for semantic search
2. **Topic Extraction**: Use AI to categorize calls (new client inquiry, existing client follow-up, dispute resolution, etc.)
3. **FAQ Generation**: Identify common questions and generate FAQ entries
4. **Training Material**: Flag exemplary calls for team training

```python
def enrich_transcript(call_id: str):
    """AI-enrich a call transcript for knowledge base."""
    call = supabase.table('call_transcripts').select('*').eq(
        'callrail_call_id', call_id
    ).single().execute()

    transcript = call.data['transcript_text']

    # Topic classification
    topics = classify_call_topic(transcript)

    # Extract Q&A pairs for FAQ
    qa_pairs = extract_qa_pairs(transcript)

    # Generate vector embeddings (chunked)
    chunks = chunk_text(transcript, chunk_size=500)
    for i, chunk in enumerate(chunks):
        embedding = generate_embedding(chunk)
        store_embedding(call.data['id'], i, chunk, embedding)

    # Update call record with enrichment
    supabase.table('call_transcripts').update({
        'topics': topics,
        'qa_pairs': qa_pairs,
        'enriched': True
    }).eq('callrail_call_id', call_id).execute()
```

---

## Cost Implications

### CallRail Subscription

| Plan | Monthly Cost | Key Features |
|------|-------------|-------------|
| Essentials | $50/mo | Call tracking, recording, 5 numbers, 250 minutes |
| Essentials + CI | $95/mo | + Conversational Intelligence (transcription, AI summaries) |
| Premium | ~$130/mo | + Advanced analytics, keyword spotting |
| Premium + CI | ~$175/mo | Full feature set |

**Conversational Intelligence (CI) is required for transcription via API.**
Without CI, the `transcription` field will be empty. Steven likely needs at minimum
the Essentials + CI plan ($95/mo) if not already subscribed.

### API Usage Costs

| Item | Cost | Notes |
|------|------|-------|
| API calls | $0 | Included in CallRail subscription |
| Webhook events | $0 | Included in CallRail subscription |
| Rate limit increases | $0 | Contact support (usually free) |

### Infrastructure Costs (Our Side)

| Component | Monthly Cost | Notes |
|-----------|-------------|-------|
| n8n processing | $0 | Self-hosted on Mac Mini |
| Supabase storage (transcripts) | ~$0.02/mo | Text data is small |
| Supabase storage (recordings) | ~$1-5/mo | MP3 files at ~1MB/min |
| OpenAI embeddings | ~$0.10/mo | For semantic search |
| **Total incremental** | **~$1-6/month** | |

### Historical Export (One-Time)

| Task | Estimated Volume | Cost |
|------|-----------------|------|
| 25 months of calls | ~2,000-5,000 calls | $0 (API included) |
| Recording downloads | ~500-2,000 with recordings | ~$2-10 storage |
| Embedding generation | ~1,000 transcripts | ~$0.50 one-time |

---

## Estimated Build Hours

| Phase | Tasks | Hours |
|-------|-------|-------|
| **Phase 1: Real-Time Webhook** | | |
| CallRail webhook setup | Configure events, URL, secret | 1-2 |
| n8n webhook receiver | Signature verify, parse payload | 3-4 |
| Supabase schema + storage | Tables, indexes, functions | 2-3 |
| Nutshell CRM sync | Match contacts, add call notes | 3-4 |
| **Phase 2: Historical Export** | | |
| Bulk export script | Paginated API calls, rate limiting | 4-6 |
| Data validation + dedup | Ensure no duplicates, handle gaps | 2-3 |
| **Phase 3: Recording Archive** | | |
| MP3 download pipeline | Fetch URLs, download, store | 3-4 |
| Supabase Storage setup | Bucket config, upload logic | 1-2 |
| **Phase 4: Knowledge Base** | | |
| Vector embeddings | Chunking, embedding generation | 3-4 |
| Topic classification | AI categorization of calls | 2-3 |
| Semantic search function | pgvector similarity search | 2-3 |
| FAQ extraction | Q&A pair mining from transcripts | 2-3 |
| Testing & QA | End-to-end testing, edge cases | 4-6 |
| **Total** | | **32-47 hours** |

### Prerequisites

- [ ] CallRail account with API access
- [ ] Conversational Intelligence plan (for transcription)
- [ ] CallRail API key (Settings > API > API Keys)
- [ ] CallRail account ID
- [ ] n8n instance with webhook capability
- [ ] Supabase project with pgvector extension
- [ ] OpenAI API key (for embeddings)

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| No CI plan = no transcripts | Core feature unavailable | Verify plan includes Conversational Intelligence |
| 25-month retention limit | Lose historical data | Export ASAP; download recordings for permanent storage |
| Rate limiting during bulk export | Slow export process | Throttle to 1 req/sec; run overnight |
| Recording URLs expire | Can't download later | Download recordings promptly; store in own storage |
| Transcript quality varies | Noisy knowledge base | Filter by auto_score; human review of low-quality |
| Webhook delivery failures | Missed call data | Nightly batch sync catches anything missed by webhook |

---

## References

- [CallRail API v3 Documentation](https://apidocs.callrail.com/)
- [CallRail Webhooks](https://support.callrail.com/hc/en-us/articles/5711246459149-Webhooks)
- [CallRail API Overview](https://support.callrail.com/hc/en-us/articles/5711821845389-CallRail-s-API)
- [CallRail API Essentials (Rollout)](https://rollout.com/integration-guides/call-rail/api-essentials)
- [CallRail Pricing](https://www.callrail.com/pricing)
- [CallRail Transcript Search](https://support.callrail.com/hc/en-us/articles/5711587905037-Transcript-search)
- [CallRail Zapier Integration](https://zapier.com/apps/callrail/integrations)

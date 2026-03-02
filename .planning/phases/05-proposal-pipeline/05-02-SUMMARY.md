---
phase: 05-proposal-pipeline
plan: 02
subsystem: proposals
tags: [ghl, crm, webhook, industry-context, hybrid-search, pitch-deck, dedup]

# Dependency graph
requires:
  - phase: 05-proposal-pipeline-plan-01
    provides: runProposalPipeline, assemblePitchDeckContent, ProposalState types, state.ts proposal DB, Telegram HITL preview
  - phase: 02-memory-and-model-routing
    provides: hybridSearch for industry context retrieval
  - phase: 03-telegram-command-channel
    provides: getBotInstance, sendMessage, escapeMarkdownV2
provides:
  - handleQualifiedLead -- GHL qualified-stage handler with dedup, contact enrichment, and pipeline dispatch
  - startWebhookListener / stopWebhookListener -- HTTP webhook endpoint on 127.0.0.1:8090 for n8n-relayed GHL events
  - searchIndustryContext -- hybrid search for industry pain points with hardcoded fallback
  - getIndustryPainPoints -- synchronous pain point lookup for plumbing/solar/dental/legal verticals
  - GHLWebhookEvent type definition for OpportunityStageUpdate payload
affects: [phase-06-per-task-rag, ghl-integration, n8n-workflows]

# Tech tracking
tech-stack:
  added: [node-http-server]
  patterns: [webhook-immediate-200, fire-and-forget-processing, industry-fallback-lookup, crm-dedup-by-contact]

key-files:
  created:
    - ~/.openclaw/src/proposals/industry-context.ts
    - ~/.openclaw/src/proposals/crm-trigger.ts
    - ~/.openclaw/src/proposals/webhook-listener.ts
    - ~/.openclaw/src/proposals/__tests__/crm-trigger.test.ts
    - ~/.openclaw/src/proposals/__tests__/webhook-listener.test.ts
  modified: []

key-decisions:
  - "Webhook listener returns 200 before reading body -- GHL retries on non-200, so immediate response prevents duplicates"
  - "Dedup via getProposalByContactId checks both trigger source match and active (non-terminal) proposal existence"
  - "Industry context search falls back to hardcoded pain points per-vertical -- safety net until memory system has content"
  - "Contact enrichment via n8n proxy with 5s timeout and graceful degradation to event data extraction"
  - "node:http createServer used directly (no Express) -- minimal dependency for single-route webhook endpoint"

patterns-established:
  - "Webhook immediate-200 pattern: respond before processing, fire-and-forget handler call"
  - "Industry fallback lookup: hybridSearch -> hardcoded pain points map -> generic defaults"
  - "CRM dedup pattern: check contactId + triggerSource before creating new proposal"
  - "n8n proxy enrichment pattern: POST to localhost relay, timeout + fallback to raw event data"

requirements-completed: [PROP-05, PROP-06]

# Metrics
duration: 6min
completed: 2026-03-02
---

# Phase 5 Plan 2: CRM-Triggered Proposals Summary

**GHL webhook listener on 127.0.0.1:8090 with qualified-stage handler, industry context via hybrid search, and automatic pitch deck generation through existing pipeline**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-02T21:09:39Z
- **Completed:** 2026-03-02T21:15:44Z
- **Tasks:** 1
- **Files modified:** 5 (5 created, 0 modified)

## Accomplishments
- HTTP webhook listener on 127.0.0.1:8090 accepting POST /webhook/ghl with immediate 200 response before async processing
- CRM trigger handler with dual dedup (same opportunity ID skip + active proposal existence check)
- Industry context retrieval via Phase 2 hybrid search with hardcoded fallback for plumbing, solar, dental, and legal verticals
- Single code path through runProposalPipeline with skipDiscovery: true -- reuses full state machine, Gamma generation, and Telegram HITL preview from Plan 05-01
- Contact enrichment via n8n GHL proxy with graceful degradation when proxy unavailable
- 48 new tests across both test files (26 CRM trigger + 22 webhook listener), zero regressions in existing 41 tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Create industry context retrieval, CRM trigger handler, and webhook listener** - `21271ec` (feat)

## Files Created/Modified
- `src/proposals/industry-context.ts` - searchIndustryContext (hybrid search + fallback) and getIndustryPainPoints (hardcoded lookup)
- `src/proposals/crm-trigger.ts` - handleQualifiedLead with dedup, contact enrichment, content assembly, and pipeline dispatch
- `src/proposals/webhook-listener.ts` - startWebhookListener/stopWebhookListener with HTTP routing and fire-and-forget processing
- `src/proposals/__tests__/crm-trigger.test.ts` - 26 tests: dedup, contact extraction, industry search, pipeline options, error handling
- `src/proposals/__tests__/webhook-listener.test.ts` - 22 tests: HTTP routing, stage matching, event filtering, async processing

## Decisions Made
- Webhook listener returns 200 before reading request body -- GHL retries on non-200 responses, so immediate acknowledgment prevents duplicate webhook deliveries
- Dedup uses dual check: first matches triggerSource containing opportunity ID, then checks for any active (non-terminal) proposal for the contact
- Industry context search falls back to hardcoded pain points when hybrid search returns no results -- ensures pitch decks always have industry-specific content
- Contact enrichment attempts n8n proxy (5s timeout) before falling back to webhook event data extraction -- graceful degradation without GHL API configuration
- Used node:http createServer directly instead of Express -- single route webhook endpoint does not need a framework

## Deviations from Plan

None - plan executed exactly as written.

## User Setup Required

**External services require manual configuration.** The following must be configured for CRM-triggered pitch decks to work:

**GHL Webhook Configuration:**
- Set `GHL_QUALIFIED_STAGE_ID` env var (GHL dashboard -> Pipelines -> qualified stage -> copy UUID)
- Set `GHL_API_KEY` env var (GHL dashboard -> Settings -> Developer -> API Keys)
- Set `GHL_LOCATION_ID` env var (GHL dashboard -> Settings -> Business Profile -> Location ID)
- Configure GHL webhook: Settings -> Webhooks -> Add -> URL: `{n8n-webhook-url}/webhook/ghl-events` -> Event: OpportunityStageUpdate

**n8n Relay Workflow:**
- Create workflow: Webhook node (path: /webhook/ghl-events) -> Switch node (route by event.type) -> HTTP Request node (POST to http://localhost:8090/webhook/ghl)

**Industry Knowledge (optional):**
- Add industry pain point markdown files to `~/.openclaw/memory/` for richer hybrid search results
- Hardcoded fallback covers plumbing, solar, dental, and legal verticals

## Issues Encountered
None.

## Next Phase Readiness
- Phase 5 (Proposal Pipeline) is fully complete: both manual pipeline (05-01) and CRM-triggered pipeline (05-02) delivered
- industry-context.ts is the single swap point when Phase 6 (Per-Task RAG) delivers per-task collections
- Webhook listener ready for production once GHL API keys and n8n relay workflow are configured
- All 89 tests pass across the full proposal module test suite

## Self-Check: PASSED

All 5 created files verified on disk. Task commit (21271ec) verified in git log.

---
*Phase: 05-proposal-pipeline*
*Completed: 2026-03-02*

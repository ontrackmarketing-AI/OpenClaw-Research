---
phase: 05-proposal-pipeline
plan: 01
subsystem: proposals
tags: [gamma, llm, sqlite, telegram, hitl, presentations, discovery-forms]

# Dependency graph
requires:
  - phase: 03-telegram-command-channel
    provides: HITL approval queue, Telegram bot, callback system, formatters
  - phase: 02-memory-and-model-routing
    provides: routeAndCall for LLM routing, cost tracking
provides:
  - ProposalAnalysis, DiscoveryForm, ProposalState type definitions
  - analyzeForProposal -- transcript to structured proposal outline
  - generateDiscoveryForm -- 8-15 question generation from meeting gaps
  - GammaMcpClient -- Gamma API wrapper with polling
  - assembleDeckContent -- structured Gamma input from analysis
  - assemblePitchDeckContent -- pitch deck from CRM contact data (for Plan 05-02)
  - SQLite proposals.db lifecycle tracking (analyzing -> delivered)
  - runProposalPipeline -- end-to-end 5-step orchestrator
  - sendProposalPreview -- RED-tier HITL approval via centralized queue
  - /proposal and /proposal_done Telegram commands
  - deliver-proposal action handler in callbacks.ts
affects: [05-proposal-pipeline-plan-02, crm-triggers, transcript-processing]

# Tech tracking
tech-stack:
  added: [gamma-mcp-api]
  patterns: [proposal-state-machine, hitl-red-tier-hardcode, pipeline-pause-at-discovery]

key-files:
  created:
    - ~/.openclaw/src/proposals/types.ts
    - ~/.openclaw/src/proposals/analyzer.ts
    - ~/.openclaw/src/proposals/discovery-form.ts
    - ~/.openclaw/src/proposals/gamma-client.ts
    - ~/.openclaw/src/proposals/assembler.ts
    - ~/.openclaw/src/proposals/state.ts
    - ~/.openclaw/src/proposals/pipeline.ts
    - ~/.openclaw/src/proposals/telegram-handlers.ts
    - ~/.openclaw/src/proposals/__tests__/analyzer.test.ts
    - ~/.openclaw/src/proposals/__tests__/assembler.test.ts
  modified:
    - ~/.openclaw/src/hitl/classify.ts
    - ~/.openclaw/src/notion/types.ts
    - ~/.openclaw/src/telegram/commands.ts
    - ~/.openclaw/src/telegram/callbacks.ts

key-decisions:
  - "Task type 'analyze-meeting' used for Sonnet routing -- 'analyze' keyword in model-routing.yaml triggers Sonnet classification"
  - "deliver-proposal hardcoded RED in classify.ts -- matches SECR-07 pattern, cannot be config-overridden"
  - "Pipeline pauses at discovery_sent status -- returns ProposalState for caller to resume after responses"
  - "sendProposalPreview routes through requestApproval (centralized HITL queue) not ad-hoc inline buttons"
  - "Gamma API called via HTTP wrapper class -- MCP protocol abstracted for future runtime swap"
  - "Telegram command /proposal_done uses underscore (Telegram converts hyphens in command names)"
  - "assemblePitchDeckContent interface defined now for Plan 05-02 CRM trigger consumption"

patterns-established:
  - "Proposal state machine: SQLite proposals.db with status transitions and auto-timestamps"
  - "Pipeline pause pattern: return partial state at discovery_sent for async resumption"
  - "RED-tier hardcode pattern: deliver-proposal alongside DELETE in classify.ts"
  - "Supplementary Telegram message pattern: approval message + edit button as separate messages"

requirements-completed: [PROP-01, PROP-02, PROP-03, PROP-04]

# Metrics
duration: 11min
completed: 2026-03-02
---

# Phase 5 Plan 1: Proposal Pipeline Core Summary

**Meeting-to-proposal pipeline with Sonnet transcript analysis, Gamma presentation generation, SQLite lifecycle tracking, and RED-tier HITL approval via Telegram**

## Performance

- **Duration:** 11 min
- **Started:** 2026-03-02T20:51:35Z
- **Completed:** 2026-03-02T21:02:36Z
- **Tasks:** 3
- **Files modified:** 14 (10 created, 4 modified)

## Accomplishments
- Full proposal pipeline: transcript analysis extracts pain points, services, pricing, competitive context, and 10-14 slide outline
- Discovery form generation with 8-15 targeted questions across 3-5 sections from meeting gaps
- Gamma MCP client with generation and polling (3s interval, 5min timeout)
- SQLite proposals.db tracking full proposal lifecycle from analyzing through delivered/rejected
- Every proposal preview routes through RED-tier centralized HITL approval queue
- /proposal and /proposal_done Telegram commands for management and edit-resume flow
- deliver-proposal action handlers wired into callbacks.ts for approve/reject state transitions

## Task Commits

Each task was committed atomically:

1. **Task 1a: Create proposal types, analyzer, and discovery form generator** - `de5a5f8` (feat)
2. **Task 1b: Create Gamma client, assembler, state machine, and extend classify/notion types** - `0720550` (feat)
3. **Task 2: Create proposal pipeline orchestrator, Telegram handlers, and /proposal command** - `f905440` (feat)

## Files Created/Modified
- `src/proposals/types.ts` - ProposalAnalysis, DiscoveryForm, ProposalState, GammaGenerationResult, pipeline option types
- `src/proposals/analyzer.ts` - analyzeForProposal() via Sonnet-tier routing with code fence stripping
- `src/proposals/discovery-form.ts` - generateDiscoveryForm() with 8-15 questions across 3-5 sections
- `src/proposals/gamma-client.ts` - GammaMcpClient class, generatePresentation with polling, listThemes, getGeneration
- `src/proposals/assembler.ts` - assembleDeckContent from analysis + discovery; assemblePitchDeckContent for CRM triggers
- `src/proposals/state.ts` - SQLite proposals.db with full lifecycle, indexes on contact_id and status
- `src/proposals/pipeline.ts` - runProposalPipeline 5-step orchestrator (create -> analyze -> discovery -> generate -> preview)
- `src/proposals/telegram-handlers.ts` - sendProposalPreview (RED-tier HITL), registerProposalCallbacks, formatDiscoveryFormMessage
- `src/proposals/__tests__/analyzer.test.ts` - 19 tests for prompt content, code fence stripping, mock parsing
- `src/proposals/__tests__/assembler.test.ts` - 22 tests for deck content assembly and pitch deck generation
- `src/hitl/classify.ts` - Added deliver-proposal hardcoded RED tier
- `src/notion/types.ts` - Added proposal-generated, proposal-approved, proposal-rejected, proposal-delivered log types
- `src/telegram/commands.ts` - Added /proposal and /proposal_done commands, updated /help
- `src/telegram/callbacks.ts` - Added deliver-proposal approve/reject action handlers in executeApprovedAction and reject path

## Decisions Made
- Task type 'analyze-meeting' chosen for Sonnet routing via keyword classification (avoids 'proposal' keyword which maps to opus)
- deliver-proposal hardcoded RED in classify.ts following the DELETE=RED SECR-07 pattern
- Pipeline pauses at discovery_sent and returns ProposalState -- caller resumes when responses arrive
- sendProposalPreview routes through requestApproval from centralized HITL queue (not custom inline buttons)
- Gamma API wrapped in HTTP client class for future MCP runtime swap
- /proposal_done uses underscore because Telegram converts hyphens in bot command names

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] routeAndCall signature mismatch -- no preferredTier option**
- **Found during:** Task 1a (analyzer.ts)
- **Issue:** Plan interfaces section showed `routeAndCall` with `{ preferredTier: 'sonnet' }` option, but actual codebase uses keyword-based classification from model-routing.yaml
- **Fix:** Used task type 'analyze-meeting' which contains 'analyze' keyword, triggering Sonnet classification per the routing config
- **Files modified:** analyzer.ts, discovery-form.ts
- **Verification:** Confirmed 'analyze' keyword is in sonnet classification rules in model-routing.yaml
- **Committed in:** de5a5f8 (Task 1a commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minimal -- adapted to actual API without changing behavior. Sonnet-tier routing achieved via keyword classification.

## User Setup Required

**External services require manual configuration.** Gamma MCP access is required for presentation generation:
- Set `GAMMA_API_KEY` environment variable (Gamma dashboard -> Settings -> API -> Generate API key, requires Pro plan $16/mo)
- Install Gamma MCP: `cd ~/.openclaw && npm install @purple-horizons/gamma-mcp`
- Add gamma entry to `~/.openclaw/.mcp.json`

## Issues Encountered
None beyond the routing signature adaptation documented above.

## Next Phase Readiness
- Plan 05-02 (CRM-triggered proposals) can consume assemblePitchDeckContent and the full pipeline
- Pipeline is ready for transcript processing integration and CRM pipeline stage triggers
- Gamma API key setup required before live testing

## Self-Check: PASSED

All 10 created files verified on disk. All 3 task commits (de5a5f8, 0720550, f905440) verified in git log.

---
*Phase: 05-proposal-pipeline*
*Completed: 2026-03-02*

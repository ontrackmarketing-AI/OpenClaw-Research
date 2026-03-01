---
phase: 01-secure-infrastructure
plan: 02
subsystem: security
tags: [n8n, proxy-workflows, hitl, content-sanitizer, tier-enforcement, webhook, yaml, typescript]

# Dependency graph
requires:
  - phase: 01-secure-infrastructure/01-01
    provides: "Docker stack with n8n container running on port 5678"
provides:
  - "6 n8n proxy workflows isolating all external API credentials from agent"
  - "Content sanitizer stripping prompt injection, hidden Unicode, and hidden HTML/CSS"
  - "HITL tier enforcement module (RED/YELLOW/GREEN classification with hardcoded DELETE=RED)"
  - "Tier configuration YAML with action-to-tier mappings"
  - "proxy-endpoints.yaml documenting all webhook URLs for agent consumption"
affects: [01-03-PLAN, 02-memory-model-routing, 03-telegram-command-channel, all-subsequent-phases]

# Tech tracking
tech-stack:
  added: [n8n-webhook-workflows, yaml-config, tsx-test-runner]
  patterns: [inline-sanitizer-per-proxy, fail-secure-default-RED, hardcoded-safety-rule, structured-json-logging]

key-files:
  created:
    - "~/.openclaw/config/hitl-tiers.yaml"
    - "~/.openclaw/src/hitl/types.ts"
    - "~/.openclaw/src/hitl/classify.ts"
    - "~/.openclaw/src/hitl/enforce.ts"
    - "~/.openclaw/src/hitl/__tests__/classify.test.ts"
    - "~/.openclaw/config/proxy-endpoints.yaml"
    - "n8n workflows: Sanitizer, proxy-clay, proxy-ghl-contacts, proxy-ghl-messages, proxy-email, proxy-dataforseo, proxy-serper"
  modified: []

key-decisions:
  - "Inline sanitizer per proxy instead of Execute Sub-Workflow -- n8n sub-workflow trigger had JSON parsing issues, inline Code node is more reliable"
  - "All 6 proxies start as stubs returning structured JSON -- ready for API key configuration without code changes"
  - "DELETE=RED hardcoded before any config lookup -- cannot be overridden by YAML (SECR-07)"
  - "Unknown actions default to RED (fail-secure) -- only explicitly listed GREEN actions auto-approve"
  - "YELLOW tier treated as RED until Phase 3 Telegram approval channel exists"
  - "Structured JSON logging for every HITL decision -- ready for observability pipeline"

patterns-established:
  - "Proxy webhook pattern: Webhook -> Sanitize Input -> Stub/API -> Respond to Webhook"
  - "Fail-secure defaults: Unknown actions are RED, not GREEN"
  - "Hardcoded safety rules override config: classify.ts checks DELETE before config lookup"
  - "Content sanitizer pipeline: injection patterns -> Unicode stripping -> HTML/CSS stripping -> truncation"
  - "Tier config as YAML: Easy to add/modify action classifications without code changes"

requirements-completed: [SECR-01, SECR-02, SECR-05, SECR-07]

# Metrics
duration: 70min
completed: 2026-02-28
---

# Phase 1 Plan 02: n8n Proxy and HITL Enforcement Summary

**6 n8n proxy workflows with inline content sanitizer and HITL tier enforcement module (RED/YELLOW/GREEN classification with hardcoded DELETE=RED rule)**

## Performance

- **Duration:** 70 min
- **Started:** 2026-02-28T23:00:08Z
- **Completed:** 2026-03-01T00:10:08Z
- **Tasks:** 2
- **Files modified:** 11 (4 TypeScript, 2 YAML configs, 1 test file, 7 n8n workflows)

## Accomplishments
- Built 6 n8n proxy workflows (clay, ghl-contacts, ghl-messages, email, dataforseo, serper) all active and responding to webhook POST requests
- Each proxy includes an inline content sanitizer that strips prompt injection patterns, invisible Unicode chars, hidden HTML/CSS, and truncates payloads > 50KB
- Created HITL tier enforcement module with 3-tier classification (RED=blocked, YELLOW=blocked, GREEN=auto-approved)
- DELETE operations are hardcoded as RED in classify.ts -- cannot be overridden by YAML config (SECR-07)
- All 28 classification tests pass covering hardcoded rules, config-based tiers, wildcards, fail-secure defaults, and enforcement behavior
- Agent process has zero API keys in environment -- all credentials will live in n8n credential store only

## Task Commits

Tasks modified infrastructure files at `~/.openclaw/` and created n8n workflows (outside this git repo). Documentation commit tracks this plan.

1. **Task 1: HITL tier configuration and enforcement module** - 4 TypeScript files + 1 YAML config + 28 passing tests
2. **Task 2: n8n proxy workflows with shared sanitizer** - 7 n8n workflows (6 proxies + 1 sanitizer reference) + proxy-endpoints.yaml

## Files Created/Modified
- `~/.openclaw/config/hitl-tiers.yaml` - Action-to-tier classification map (RED/YELLOW/GREEN)
- `~/.openclaw/src/hitl/types.ts` - TypeScript type definitions for HITL system
- `~/.openclaw/src/hitl/classify.ts` - Tier classification with hardcoded DELETE=RED rule
- `~/.openclaw/src/hitl/enforce.ts` - HITL enforcement, config loading, structured JSON logging
- `~/.openclaw/src/hitl/__tests__/classify.test.ts` - 28 test cases covering all classification and enforcement scenarios
- `~/.openclaw/config/proxy-endpoints.yaml` - Webhook URL documentation for agent consumption
- `n8n: Sanitizer` - Reference sub-workflow with sanitizer code (ID: mGVJKoCoRAAMh5iZ)
- `n8n: proxy-clay` - Clay enrichment proxy (ID: drSoXYOXm0Uuz3yJ)
- `n8n: proxy-ghl-contacts` - GoHighLevel contacts proxy (ID: eAbaxdnhZthZZSBO)
- `n8n: proxy-ghl-messages` - GoHighLevel messages proxy (ID: ji5BLL4C5f9jPfwB)
- `n8n: proxy-email` - Email sending proxy (ID: hdIYfd7cjGEO8YKN)
- `n8n: proxy-dataforseo` - DataForSEO proxy (ID: cE3pHxXiFjtQxvwX)
- `n8n: proxy-serper` - Serper search proxy (ID: KrtYtiw1o17TweEg)

## Decisions Made
- **Inline sanitizer per proxy:** n8n's Execute Sub-Workflow trigger had JSON serialization issues with the Code node output. Embedded the sanitizer as an inline Code node in each proxy workflow instead. Same security guarantee -- every request is sanitized -- with more reliable execution.
- **All proxies as stubs:** Per plan instructions, all 6 proxies return structured stub responses since API keys aren't configured yet. Each stub includes TODO comments marking where to add the HTTP Request node with credentials.
- **DELETE hardcode first:** classify.ts checks `action.toLowerCase().includes('delete')` before consulting any config. This prevents any config override from weakening the safety rule (SECR-07).
- **Fail-secure default RED:** Any action not explicitly listed in the YAML tiers defaults to RED. Only known-safe actions in the GREEN tier auto-approve.
- **YELLOW = blocked:** Until the Phase 3 Telegram approval channel exists, YELLOW-tier actions are treated as RED (blocked with explanation).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] n8n API authentication required API key, not basic auth**
- **Found during:** Task 2 (pre-flight)
- **Issue:** n8n v2.5.2 REST API requires X-N8N-API-KEY header or cookie-based session auth, not HTTP Basic Auth
- **Fix:** Used cookie-based authentication via /rest/login endpoint with session cookies
- **Verification:** All workflow CRUD operations succeeded with cookie auth

**2. [Rule 3 - Blocking] n8n Execute Sub-Workflow JSON parsing failure**
- **Found during:** Task 2 (workflow creation)
- **Issue:** Execute Sub-Workflow node reported "Unexpected end of JSON input" when calling the Sanitizer sub-workflow. The workflowJson parameter was resolving to `"\n\n\n"` instead of actual workflow content.
- **Fix:** Replaced Execute Sub-Workflow pattern with inline Code node containing the sanitizer logic in each proxy workflow. Same security guarantee, more reliable execution.
- **Verification:** All 6 proxies return sanitized responses with correct flag detection

**3. [Rule 1 - Bug] Regex syntax error in sanitizer style block pattern**
- **Found during:** Task 2 (workflow testing)
- **Issue:** Double-escaped regex `[\\\\s\\\\S]*?` in the style block pattern caused "Invalid regular expression flags" error in n8n's Code node VM
- **Fix:** Corrected escape levels to `[\\s\\S]*?` for proper regex in the n8n execution context
- **Verification:** Sanitizer processes all test payloads without errors

**4. [Rule 3 - Blocking] n8n workflow activation required versionId parameter**
- **Found during:** Task 2 (workflow activation)
- **Issue:** PATCH with `{active: true}` returned 200 but workflow stayed inactive. Activation endpoint `/rest/workflows/{id}/activate` required versionId field.
- **Fix:** Used POST to `/rest/workflows/{id}/activate` with `{versionId: "..."}` from workflow creation response
- **Verification:** All 6 proxy workflows confirmed active=true

---

**Total deviations:** 4 auto-fixed (1 bug, 3 blocking)
**Impact on plan:** All auto-fixes were necessary to work with n8n v2.5.2 REST API. Architecture unchanged -- inline sanitizer provides identical security properties to the sub-workflow approach. No scope creep.

## Issues Encountered
- n8n v2.5.2 internal REST API documentation is sparse -- required trial-and-error to discover correct field names (emailOrLdapLoginId, versionId for activation)
- Duplicate workflows accumulated during debugging -- cleaned up by deleting all existing workflows before final creation

## User Setup Required
None - no external service configuration required. All 6 proxies are stubs awaiting API key configuration in n8n credential store.

## Next Phase Readiness
- HITL enforcement module ready for integration into agent action pipeline
- All 6 proxy webhooks active and testable at http://localhost:5678/webhook/proxy-{service}
- Content sanitizer proven to detect and strip injection patterns
- Phase 1 Plan 03 (cost circuit breakers) already completed -- Phase 1 is now complete
- Ready to proceed to Phase 2: Memory and Model Routing

## Self-Check: PASSED

All files verified:
- FOUND: ~/.openclaw/config/hitl-tiers.yaml
- FOUND: ~/.openclaw/src/hitl/types.ts
- FOUND: ~/.openclaw/src/hitl/classify.ts
- FOUND: ~/.openclaw/src/hitl/enforce.ts
- FOUND: ~/.openclaw/src/hitl/__tests__/classify.test.ts
- FOUND: ~/.openclaw/config/proxy-endpoints.yaml
- FOUND: .planning/phases/01-secure-infrastructure/01-02-SUMMARY.md
- n8n: 6 active proxy workflows responding correctly
- n8n: Sanitizer inline Code node detecting injection patterns
- Tests: 28/28 passing

---
*Phase: 01-secure-infrastructure*
*Completed: 2026-02-28*

# Phase 5: Proposal Pipeline - Research

**Researched:** 2026-03-02
**Domain:** Meeting transcript analysis, discovery form generation, Gamma MCP presentation automation, GHL CRM-triggered decks, HITL approval via Telegram
**Confidence:** HIGH (Gamma MCP verified via official docs), MEDIUM (GHL webhook relay, discovery form approach), MEDIUM (CRM trigger architecture)

## Summary

Phase 5 automates the meeting-to-proposal workflow: transcript analysis produces a slide outline and discovery form, discovery form responses feed into a Gamma presentation, and every external deliverable passes through Telegram HITL approval before reaching a prospect. The second half handles CRM-triggered decks -- when a lead moves to "qualified" in GHL, the agent automatically drafts a tailored pitch deck using industry-specific context from client knowledge RAG.

The core integration is the Gamma MCP server, which provides 5 tools: `gamma_generate`, `gamma_get_generation`, `gamma_create_from_template`, `gamma_list_themes`, and `gamma_list_folders`. The server is installed via npm (`@purple-horizons/gamma-mcp`) and authenticated with an API key (`sk-gamma-xxxxxxxx`) from a Gamma Pro or higher account. Gamma uses a credit system (~1-5 credits per card, 2-125 credits per image depending on model). A 12-slide pitch deck with basic AI images costs approximately 20-60 credits.

The transcript analysis reuses the Phase 4 extraction pipeline (`extractFromTranscript`) but adds a proposal-specific prompt that extracts pain points, proposed services, pricing signals, and competitive context. Discovery forms are generated as structured question sets by the LLM and delivered via a simple hosted form (GHL form or a lightweight custom page) -- GHL does not have a programmatic form creation API, so the form content is generated and the operator sends the link manually (HITL gate). CRM triggers come from GHL `OpportunityStageUpdate` webhooks relayed through n8n to OpenClaw.

**Primary recommendation:** Use the `@purple-horizons/gamma-mcp` npm package for Gamma integration (5 verified tools, MIT license), reuse the Phase 4 transcript extraction with a proposal-specific prompt, generate discovery form content via LLM (Sonnet tier for quality), deliver CRM triggers via n8n webhook relay from GHL, and gate every external deliverable through the Phase 3 Telegram HITL approval system.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PROP-01 | Agent processes a meeting recording into a slide outline using Claude analysis | Reuses Phase 4 `extractFromTranscript()` with a proposal-specific extraction prompt. Sonnet tier for quality. Outputs structured JSON with pain_points, services, pricing_structure, competitive_context, and slide_outline array. |
| PROP-02 | Agent generates a discovery form from meeting context and sends it to the prospect | LLM generates structured question set from meeting context. Delivered as a GHL survey link or simple hosted form. Operator sends the link (HITL gate -- form delivery is external communication). |
| PROP-03 | Agent generates a Gamma presentation using saved theme from discovery form responses + meeting context | `gamma_generate` MCP tool with `themeId` from saved client brand config. InputText assembled from meeting analysis + discovery responses. Poll `gamma_get_generation` for completion. Returns `gammaUrl` preview link. |
| PROP-04 | User reviews Gamma preview link via Telegram before any proposal is delivered -- always HITL Tier 1 | Reuses Phase 3 HITL approval queue (`requestApproval`). Preview link sent as Telegram message with Approve/Edit/Reject inline keyboard. RED-tier classification for proposal delivery (SECR-07 pattern). |
| PROP-05 | Moving a lead to "qualified" in GHL automatically triggers a tailored pitch deck draft | GHL `OpportunityStageUpdate` webhook relayed through n8n to OpenClaw webhook listener. Listener checks `pipelineStageId` matches "qualified" stage, pulls contact data from GHL MCP, triggers proposal generation. |
| PROP-06 | CRM-triggered decks include industry-specific context pulled from client knowledge RAG | Qdrant vector search on client knowledge collection (built in Phase 6, but basic memory search via Phase 2 hybrid search available now). Industry context from GHL contact custom fields (`industry`, `pain_signals`, `tech_stack`). |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @purple-horizons/gamma-mcp | latest | Gamma MCP server -- presentation generation, theme listing, folder management | Official community MCP server with 5 tools, MIT license, verified against Gamma Generate API v1.0 (GA since Nov 2025). |
| grammy | 1.41.x | Telegram bot -- HITL approval for proposal delivery | Already installed (Phase 3). Reuse for preview link delivery and approve/reject flow. |
| @notionhq/client | 5.11.x | Notion API -- action log for proposal events | Already installed (Phase 3). Log proposal generation, approval, delivery events. |
| better-sqlite3 | 12.x | Proposal state tracking -- generation queue, approval status | Already installed (Phase 1). Track proposal lifecycle: generated -> previewed -> approved -> delivered. |
| express or http module | Built-in | Webhook listener for GHL events via n8n | Node built-in http or lightweight express for POST endpoint. Receives n8n-relayed GHL webhooks. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| GoHighLevel MCP | Existing | CRM contact/opportunity data for pitch deck context | Already built (Windows machine). Pull contact, opportunity, and pipeline data for deck assembly. |
| uuid | 10.x | Unique IDs for proposal tracking | Already installed. Proposal IDs, generation tracking. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Gamma MCP (`gamma_generate`) | python-pptx for local generation | python-pptx gives full template control but requires design work. Gamma provides AI-designed layouts with zero design effort. Use python-pptx only for strict template-locked recurring reports. |
| Gamma MCP (`gamma_create_from_template`) | `gamma_generate` with detailed inputText | Template-based generation preserves exact layout/structure, generate is more flexible. Use templates for repeatable pitch deck format, generate for ad-hoc proposals. |
| GHL webhook via n8n relay | Direct Tailscale Funnel for webhooks | n8n relay adds a hop but provides event buffering, pre-processing, and GHL's webhook URL already points to n8n. Direct funnel would require reconfiguring GHL webhooks. |
| LLM-generated discovery form content | GHL native form builder API | GHL has no programmatic form creation API. LLM generates the question set; operator creates/sends the form via GHL dashboard or shared link. |
| Sonnet tier for proposal content | Haiku tier | Proposals are client-facing (MODL-01 routing rules: client-facing -> higher quality tier). Sonnet provides better reasoning for pain point analysis and service recommendations. |

**Installation:**
```bash
# Gamma MCP server
cd ~/.openclaw && npm install @purple-horizons/gamma-mcp

# No other new packages needed -- all dependencies installed from Phases 1-4
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── proposals/
│   ├── types.ts              # ProposalState, SlideOutline, DiscoveryForm types
│   ├── analyzer.ts           # Meeting transcript -> proposal outline extraction
│   ├── discovery-form.ts     # Discovery form question generation from meeting context
│   ├── gamma-client.ts       # Gamma MCP wrapper -- generate, poll, theme selection
│   ├── assembler.ts          # Combine meeting context + discovery responses into deck input
│   ├── pipeline.ts           # Orchestrator -- end-to-end meeting-to-proposal flow
│   ├── crm-trigger.ts        # GHL webhook handler for qualified stage change
│   ├── webhook-listener.ts   # HTTP endpoint for n8n-relayed GHL webhooks
│   └── __tests__/
│       ├── analyzer.test.ts
│       ├── assembler.test.ts
│       └── gamma-client.test.ts
├── transcripts/              # [EXISTING] -- reuse extractFromTranscript
├── hitl/                     # [EXISTING] -- reuse requestApproval, approval queue
├── telegram/                 # [EXISTING] -- extend with proposal preview callbacks
├── notion/                   # [EXISTING] -- log proposal events to action log
├── router/                   # [EXISTING] -- LLM calls for analysis and form generation
├── memory/                   # [EXISTING] -- client knowledge retrieval for deck context
└── todo/                     # [EXISTING] -- track follow-up tasks from proposals
```

### Pattern 1: Meeting Transcript -> Proposal Outline

**What:** Reuse the Phase 4 `extractFromTranscript()` pipeline with a proposal-specific prompt. Instead of generic action items and decisions, extract pain points, proposed services, pricing signals, competitive intelligence, and a structured slide outline.

**When to use:** After a meeting recording is processed (PROP-01).

**Example:**
```typescript
// Source: Phase 4 extraction pattern + Gamma MCP docs
import { routeAndCall } from '../router/router.js';

const PROPOSAL_EXTRACTION_PROMPT = `Analyze this meeting transcript and extract proposal-relevant information.

Return JSON with:
{
  "pain_points": [{"pain": "...", "severity": "high|medium|low", "evidence": "..."}],
  "proposed_services": [{"service": "...", "rationale": "...", "priority": "primary|secondary"}],
  "pricing_signals": {"budget_mentioned": boolean, "range": "...", "willingness": "high|medium|low|unknown"},
  "competitive_context": {"current_agency": "...", "competitors_mentioned": [], "switching_reason": "..."},
  "prospect_info": {"company": "...", "contact_name": "...", "industry": "...", "size": "..."},
  "slide_outline": [
    {"slide_num": 1, "title": "...", "type": "cover|problem|solution|services|case-study|pricing|cta", "key_points": ["..."]}
  ],
  "discovery_gaps": ["Questions that should be asked in discovery form"]
}

Rules:
- Pain points must cite evidence from the transcript ("they said X" or "they mentioned Y")
- Services should map to OnTrack Marketing offerings: SEO, PPC, Social Media, Web Design, Review Management, Content Marketing
- Slide outline should be 10-14 slides
- Discovery gaps are questions where the meeting didn't provide enough info

Transcript:
`;

export async function analyzeForProposal(
  transcriptText: string,
  sessionId: string
): Promise<ProposalAnalysis> {
  const result = await routeAndCall(
    'proposal-analysis',
    [{ role: 'user', content: PROPOSAL_EXTRACTION_PROMPT + transcriptText }],
    '',
    sessionId,
    { preferredTier: 'sonnet' }  // Client-facing quality
  );

  const content = result.content
    .replace(/^```(?:json)?\s*\n?/, '')
    .replace(/\n?```\s*$/, '');

  return JSON.parse(content) as ProposalAnalysis;
}
```

### Pattern 2: Discovery Form Generation

**What:** LLM generates a structured set of discovery questions based on the meeting analysis. Questions target the gaps identified during transcript analysis plus standard discovery questions for the prospect's industry.

**When to use:** After meeting analysis identifies discovery gaps (PROP-02).

**Example:**
```typescript
const DISCOVERY_FORM_PROMPT = `Generate a discovery form for a marketing agency prospect meeting follow-up.

Context from meeting:
{meetingContext}

Generate a JSON discovery form with 8-15 questions:
{
  "form_title": "Discovery Questionnaire - {company}",
  "intro_text": "Thank you for meeting with us...",
  "sections": [
    {
      "section_name": "Business Goals",
      "questions": [
        {
          "id": "q1",
          "text": "...",
          "type": "text|multiple_choice|scale|yes_no",
          "options": ["..."],  // for multiple_choice
          "required": true
        }
      ]
    }
  ]
}

Rules:
- Address the discovery gaps from the meeting analysis
- Include standard questions: current marketing budget, biggest challenges, timeline, decision-makers
- Questions should feel conversational, not interrogative
- Include 1-2 questions about competitor awareness
- Scale questions should use 1-5 with labels
`;

export async function generateDiscoveryForm(
  meetingAnalysis: ProposalAnalysis,
  sessionId: string
): Promise<DiscoveryForm> {
  const context = JSON.stringify({
    prospect: meetingAnalysis.prospect_info,
    pain_points: meetingAnalysis.pain_points,
    discovery_gaps: meetingAnalysis.discovery_gaps,
    proposed_services: meetingAnalysis.proposed_services,
  });

  const prompt = DISCOVERY_FORM_PROMPT.replace('{meetingContext}', context)
    .replace('{company}', meetingAnalysis.prospect_info.company);

  const result = await routeAndCall(
    'discovery-form-gen',
    [{ role: 'user', content: prompt }],
    '',
    sessionId,
    { preferredTier: 'sonnet' }
  );

  const content = result.content
    .replace(/^```(?:json)?\s*\n?/, '')
    .replace(/\n?```\s*$/, '');

  return JSON.parse(content) as DiscoveryForm;
}
```

### Pattern 3: Gamma MCP Presentation Generation

**What:** Use the Gamma MCP `gamma_generate` tool to create a presentation from assembled content. Poll `gamma_get_generation` until complete. Send preview link to Telegram for HITL approval.

**When to use:** After assembling deck content from meeting analysis + discovery responses (PROP-03, PROP-05).

**Example:**
```typescript
// Source: Gamma MCP docs (developers.gamma.app) + Purple-Horizons/gamma-mcp README
import { requestApproval } from '../hitl/approval-queue.js';

export async function generatePresentation(
  inputText: string,
  options: {
    themeId?: string;
    numCards?: number;
    format?: 'presentation' | 'document';
    exportAs?: 'pdf' | 'pptx';
    textTone?: string;
    textAudience?: string;
  }
): Promise<GammaGenerationResult> {
  // Call Gamma MCP generate tool
  const generation = await gammaMcp.gamma_generate({
    inputText,
    textMode: 'generate',
    format: options.format || 'presentation',
    themeId: options.themeId,
    numCards: options.numCards || 12,
    textAmount: 'medium',
    textTone: options.textTone || 'professional, confident',
    textAudience: options.textAudience,
    imageSource: 'aiGenerated',
    dimensions: '16x9',
  });

  // Poll for completion (timeout 5 minutes)
  const startTime = Date.now();
  const TIMEOUT_MS = 5 * 60 * 1000;
  let status;

  while (Date.now() - startTime < TIMEOUT_MS) {
    status = await gammaMcp.gamma_get_generation({
      generationId: generation.generationId,
    });

    if (status.status === 'completed') {
      return {
        generationId: generation.generationId,
        gammaUrl: status.gammaUrl,
        credits: status.credits,
      };
    }

    await new Promise(resolve => setTimeout(resolve, 3000)); // Poll every 3s
  }

  throw new Error(`Gamma generation timed out after ${TIMEOUT_MS / 1000}s`);
}
```

### Pattern 4: CRM-Triggered Deck via GHL Webhook

**What:** GHL fires an `OpportunityStageUpdate` webhook when a lead moves to "qualified". n8n relays this to OpenClaw's webhook listener. OpenClaw pulls contact data, assembles industry context, generates a pitch deck, and posts the preview to Telegram for approval.

**When to use:** PROP-05 CRM-triggered automatic deck generation.

**Example:**
```typescript
// Source: GHL webhook docs (marketplace.gohighlevel.com)
import { createServer } from 'node:http';

const QUALIFIED_STAGE_ID = process.env.GHL_QUALIFIED_STAGE_ID;

export function startWebhookListener(port: number = 8090): void {
  const server = createServer(async (req, res) => {
    if (req.method !== 'POST' || req.url !== '/webhook/ghl') {
      res.writeHead(404);
      res.end();
      return;
    }

    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ status: 'received' }));

      try {
        const event = JSON.parse(body);
        if (event.type === 'OpportunityStageUpdate' &&
            event.pipelineStageId === QUALIFIED_STAGE_ID) {
          await handleQualifiedLead(event);
        }
      } catch (err) {
        console.error(JSON.stringify({
          level: 'error',
          component: 'webhook-listener',
          action: 'process_webhook',
          error: (err as Error).message,
        }));
      }
    });
  });

  server.listen(port, '127.0.0.1', () => {
    console.error(JSON.stringify({
      level: 'info',
      component: 'webhook-listener',
      action: 'started',
      port,
    }));
  });
}

async function handleQualifiedLead(event: GHLWebhookEvent): Promise<void> {
  // 1. Pull contact data from GHL MCP
  const contact = await ghlMcp.get_contact({ contactId: event.contactId });

  // 2. Search memory for industry context
  const industryContext = await memorySearch(
    `${contact.industry} marketing pain points case studies`
  );

  // 3. Assemble pitch deck content
  const inputText = assemblePitchDeckContent(contact, industryContext);

  // 4. Generate via Gamma
  const result = await generatePresentation(inputText, {
    numCards: 12,
    textTone: 'professional, persuasive',
    textAudience: `${contact.industry} business owner`,
  });

  // 5. Send to Telegram for HITL approval (Tier 1 -- RED)
  await requestApproval(
    {
      action: 'deliver-proposal',
      params: {
        contactId: event.contactId,
        contactName: `${contact.firstName} ${contact.lastName}`,
        company: contact.companyName,
        gammaUrl: result.gammaUrl,
        generationId: result.generationId,
      },
      source: 'crm-trigger:qualified',
      timestamp: new Date(),
    },
    bot,
    operatorChatId
  );
}
```

### Pattern 5: HITL Approval for Proposals (Tier 1)

**What:** Every proposal preview is sent to Telegram with Approve/Edit/Reject buttons. Proposal delivery to prospects is classified as RED-tier (external communication, reputation-affecting). No proposal reaches a prospect without explicit HITL approval.

**When to use:** Every proposal (PROP-04). No exceptions.

**Example:**
```typescript
// Source: Phase 3 HITL approval pattern
// Extend the existing approval message format for proposals
export function formatProposalApprovalMessage(
  proposal: ProposalPreview
): string {
  const e = escapeMarkdownV2;
  return [
    `*Proposal Ready for Review*`,
    ``,
    `*Client:* ${e(proposal.clientName)}`,
    `*Company:* ${e(proposal.company)}`,
    `*Type:* ${e(proposal.type)}`,
    `*Slides:* ${e(String(proposal.slideCount))}`,
    ``,
    `[Preview in Gamma](${e(proposal.gammaUrl)})`,
    ``,
    `_Tap a button below\\. No proposal is sent without your approval\\._`,
  ].join('\n');
}

// Register proposal-specific callbacks
export function registerProposalCallbacks(bot: Bot): void {
  bot.callbackQuery(/^proposal:(approve|edit|reject):(.+)$/, async (ctx) => {
    const [, decision, proposalId] = ctx.match!;

    if (decision === 'approve') {
      // Mark approved, export PDF/PPTX, notify operator it's ready to send
      await updateProposalStatus(proposalId, 'approved');
      await ctx.editMessageText(
        `Proposal approved\\. Ready for delivery\\.`,
        { parse_mode: 'MarkdownV2' }
      );
    } else if (decision === 'edit') {
      // Direct operator to Gamma editor
      const proposal = await getProposal(proposalId);
      await ctx.editMessageText(
        `Edit in Gamma: ${escapeMarkdownV2(proposal.gammaUrl)}\n` +
        `Send /proposal\\-done ${escapeMarkdownV2(proposalId)} when ready\\.`,
        { parse_mode: 'MarkdownV2' }
      );
    } else if (decision === 'reject') {
      await updateProposalStatus(proposalId, 'rejected');
      await ctx.editMessageText(
        `Proposal rejected and archived\\.`,
        { parse_mode: 'MarkdownV2' }
      );
    }
  });
}
```

### Anti-Patterns to Avoid

- **Sending proposals without HITL approval:** Proposals represent agency reputation. Always RED-tier classification. No automated delivery path, ever. This matches the explicit Out of Scope rule: "Automatic proposal delivery -- Proposals represent agency reputation; always HITL Tier 1."
- **Using Haiku tier for proposal content generation:** Proposal outlines and discovery forms are client-facing. Route to Sonnet (or Opus for high-value prospects) per MODL-01 routing rules.
- **Generating the full deck text locally then using Gamma `preserve` mode:** Gamma's `generate` mode produces better layouts when given an outline with key points. Let Gamma's AI handle text expansion and layout decisions. Use `preserve` only when exact wording is critical.
- **Blocking on GHL webhook delivery:** Always return 200 immediately from the webhook endpoint, then process asynchronously. GHL retries on non-200 responses and you don't want duplicate triggers.
- **Storing discovery form responses outside the CRM:** Discovery responses should be logged as GHL contact notes or custom fields so the full prospect history lives in one place. OpenClaw processes them but doesn't become the system of record for customer data.
- **Hardcoding the "qualified" stage ID:** GHL pipeline stage IDs are UUIDs that vary per account. Read from environment variable (`GHL_QUALIFIED_STAGE_ID`) or query the pipeline stages at startup.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Presentation generation | Custom slide rendering (python-pptx, Google Slides) | Gamma MCP `gamma_generate` | Gamma produces AI-designed layouts, handles responsive cards, image generation, and theming. Custom rendering requires weeks of design work for comparable quality. |
| Presentation theming | Custom color/font application logic | Gamma `gamma_list_themes` + `themeId` parameter | Gamma has a curated theme library. Select by keyword match, apply with one parameter. |
| Template-based decks | Build a template engine | Gamma `gamma_create_from_template` | Create one good template in Gamma, then replicate it programmatically with different content via the MCP tool. |
| Webhook URL exposure | Custom reverse proxy or ngrok | n8n webhook relay (already running) | n8n already has a reachable URL for GHL webhooks. Relay to local OpenClaw endpoint. No new infrastructure. |
| Form builder | Custom HTML form generator | GHL native forms/surveys + LLM-generated content | GHL has built-in form/survey tools with CRM integration. Agent generates the question content; operator creates the form in GHL dashboard. |
| Proposal state machine | In-memory state tracking | SQLite proposals table (better-sqlite3) | Proposals have a multi-day lifecycle (generated -> previewed -> approved -> delivered). Must survive restarts. |

**Key insight:** This phase is an orchestration phase, not a build-from-scratch phase. The heavy lifting (presentation generation, CRM data, HITL approval, transcript extraction) is already built or available as MCP tools. The value is in connecting these pieces with the right prompts and the right gates.

## Common Pitfalls

### Pitfall 1: Gamma API Key and Credit Management
**What goes wrong:** Generation fails with "insufficient credits" error mid-proposal flow.
**Why it happens:** Gamma uses a credit system. A 12-slide deck with AI images consumes 20-60 credits. Monthly credit allowance varies by plan tier (Pro vs Ultra vs Teams).
**How to avoid:** Check credit balance before generation (query `gamma_get_generation` credits field). Set up auto-recharge on the Gamma billing page. Monitor credit consumption per proposal and alert if approaching limit. Use `noImages` or `pexels` for draft previews, save AI image credits for final approved decks.
**Warning signs:** `gamma_generate` returns error with "insufficient credits" message.

### Pitfall 2: Gamma Generation Timeout
**What goes wrong:** `gamma_get_generation` never returns `completed` status, proposal flow hangs.
**Why it happens:** Complex decks (15+ cards with AI images) can take 2-5 minutes. Network issues or Gamma service load can extend this.
**How to avoid:** Poll with 3-second intervals. Hard timeout at 5 minutes. On timeout: notify operator via Telegram with partial status, offer retry button. Never block the main event loop -- poll in a background async function.
**Warning signs:** Generation takes >3 minutes consistently; status remains "pending" after timeout.

### Pitfall 3: GHL Webhook Duplicate Events
**What goes wrong:** The same "qualified" stage change fires multiple times, generating duplicate pitch decks.
**Why it happens:** GHL may retry webhooks on timeout or network issues. n8n relay may also retry. Additionally, moving a lead back and forth in the pipeline re-triggers the webhook.
**How to avoid:** Track processed webhook events by opportunity ID + stage ID in SQLite. Before processing, check if this exact transition was already handled. Idempotency key: `${opportunityId}:${pipelineStageId}:${dateAdded}`.
**Warning signs:** Multiple pitch decks generated for the same prospect; duplicate Telegram approval messages.

### Pitfall 4: Discovery Form Response Ingestion
**What goes wrong:** Discovery form responses arrive but the agent can't match them to the original meeting/proposal.
**Why it happens:** GHL form submissions arrive as webhooks with contact IDs but no explicit link to the original meeting transcript or proposal analysis.
**How to avoid:** Store the proposal state with `contactId` as a foreign key. When a form submission arrives, look up the pending proposal by contactId. Include the proposal ID in a hidden form field if possible. Fall back to contact-based matching.
**Warning signs:** Form responses processed but not connected to any proposal; orphaned proposal states.

### Pitfall 5: Client Knowledge RAG Not Available Yet
**What goes wrong:** PROP-06 requires industry-specific context from "client knowledge RAG" but Per-Task RAG is Phase 6.
**Why it happens:** Phase 5 depends on Phase 4 (complete) but PROP-06 references RAG capabilities planned for Phase 6.
**How to avoid:** Use Phase 2's existing hybrid search (FTS5 + Qdrant) on `~/.openclaw/memory/` as a lightweight substitute. Index industry pain points, case studies, and service descriptions in the existing memory system. When Phase 6 delivers per-task RAG collections, swap the search target. The abstraction should be: `searchClientKnowledge(industry, keywords)` returning relevant context strings.
**Warning signs:** Pitch decks lack industry-specific detail; all decks look generic regardless of prospect industry.

### Pitfall 6: Gamma MCP Server Configuration
**What goes wrong:** MCP tool calls to Gamma fail silently or return connection errors.
**Why it happens:** The Gamma MCP server requires explicit configuration in the MCP server registry (`.mcp.json` or equivalent), the `GAMMA_API_KEY` environment variable, and the npm package to be installed and built.
**How to avoid:** During setup: install `@purple-horizons/gamma-mcp`, add to MCP config, set `GAMMA_API_KEY`, test with a simple `gamma_list_themes` call before any generation. Verify the MCP server starts without errors.
**Warning signs:** "Tool not found" errors; MCP server process crashes on startup.

### Pitfall 7: Proposal Content Quality Control
**What goes wrong:** Generated proposals contain generic or incorrect information about the prospect's business.
**Why it happens:** LLM hallucination when given sparse meeting context. Gamma's AI text generation adds plausible-sounding but unverified claims.
**How to avoid:** Use `textMode: 'generate'` with detailed inputText that includes only verified facts from the meeting transcript. Never generate pricing without explicit operator input. Flag any AI-generated claims with "[verify]" markers in the outline. The HITL review step catches these, but reducing hallucination input reduces review burden.
**Warning signs:** Operator consistently edits or rejects proposals for factual errors; approval rate drops below 80%.

## Code Examples

Verified patterns from official sources:

### Gamma MCP Tool Calls
```typescript
// Source: developers.gamma.app/docs + Purple-Horizons/gamma-mcp README

// 1. List themes to find a match for client branding
const themes = await gammaMcp.gamma_list_themes({
  query: 'professional',
  limit: 10,
});
// Returns: { data: [{ id: "...", name: "...", type: "standard" }], hasMore: false }

// 2. Generate a presentation
const generation = await gammaMcp.gamma_generate({
  inputText: `Create a marketing pitch deck for Acme Plumbing.
    Pain Points: No website, zero Google reviews, competitors running Google Ads.
    Proposed Services: Website design, Google Business Profile optimization, Review management.
    Pricing: $1,500/mo starter, $2,500/mo growth, $4,000/mo premium.
    Include case study from similar plumbing client.`,
  textMode: 'generate',
  format: 'presentation',
  themeId: themes.data[0]?.id,
  numCards: 12,
  textAmount: 'medium',
  textTone: 'professional, confident, data-driven',
  textAudience: 'plumbing business owner considering marketing agency',
  imageSource: 'aiGenerated',
  dimensions: '16x9',
});
// Returns: { generationId: "abc123" }

// 3. Poll for completion
let status;
do {
  await new Promise(r => setTimeout(r, 3000));
  status = await gammaMcp.gamma_get_generation({
    generationId: generation.generationId,
  });
} while (status.status === 'pending');
// Returns: { status: "completed", gammaUrl: "https://gamma.app/docs/...", credits: { deducted: 45, remaining: 2955 } }

// 4. Create from template (for repeatable pitch deck format)
const fromTemplate = await gammaMcp.gamma_create_from_template({
  gammaId: 'g_pitch_deck_template_123',  // Pre-created OnTrack Marketing template
  prompt: `Adapt this pitch deck for Acme Plumbing.
    Industry: Plumbing. Location: Austin, TX.
    Pain points: No website, low Google reviews.
    Recommended services: Web design, SEO, Review management.`,
  themeId: themes.data[0]?.id,
  exportAs: 'pdf',
});
```

### GHL OpportunityStageUpdate Webhook Payload
```typescript
// Source: marketplace.gohighlevel.com/docs/webhook/OpportunityStageUpdate
interface GHLOpportunityStageUpdate {
  type: 'OpportunityStageUpdate';
  locationId: string;       // Sub-account ID
  id: string;               // Opportunity ID
  assignedTo: string;       // Assigned user ID
  contactId: string;        // Contact ID -- use to pull full contact data
  monetaryValue: number;    // Deal value
  name: string;             // Opportunity name
  pipelineId: string;       // Pipeline ID
  pipelineStageId: string;  // New stage ID (UUID)
  source: string;           // Lead source
  status: string;           // 'open' | 'won' | 'lost' | 'abandoned'
  dateAdded: string;        // ISO 8601 timestamp
}
```

### Proposal State Machine
```typescript
// Source: better-sqlite3 pattern from Phase 1
import Database from 'better-sqlite3';

const db = new Database(
  path.join(process.env.HOME!, '.openclaw/data/proposals.db')
);

db.exec(`
  CREATE TABLE IF NOT EXISTS proposals (
    id TEXT PRIMARY KEY,
    contact_id TEXT NOT NULL,
    contact_name TEXT,
    company TEXT,
    type TEXT NOT NULL DEFAULT 'pitch_deck',
    status TEXT NOT NULL DEFAULT 'analyzing',
    meeting_analysis TEXT,
    discovery_form TEXT,
    discovery_responses TEXT,
    gamma_generation_id TEXT,
    gamma_url TEXT,
    theme_id TEXT,
    telegram_message_id INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    approved_at TEXT,
    delivered_at TEXT,
    rejection_reason TEXT,
    trigger_source TEXT
  );
  CREATE INDEX IF NOT EXISTS idx_proposals_contact ON proposals(contact_id);
  CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals(status);
`);

// Status transitions:
// analyzing -> outline_ready -> discovery_sent -> discovery_received -> generating -> preview_sent -> approved -> delivered
// analyzing -> outline_ready -> generating -> preview_sent -> approved -> delivered  (skip discovery)
// Any status -> rejected (terminal)
// Any status -> expired (after 30 days)
```

### n8n Webhook Relay Configuration
```
n8n Workflow: "GHL to OpenClaw Relay"

[Webhook Node]
  URL: /webhook/ghl-events
  Method: POST
  Response Code: 200

  -> [Switch Node: Route by event.type]
     -> "OpportunityStageUpdate": [HTTP Request Node]
        Method: POST
        URL: http://localhost:8090/webhook/ghl
        Body: {{ $json }}
        Timeout: 5000ms
     -> Other events: [No Operation] (future expansion)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Gamma connector (Claude Desktop only) | Gamma MCP server (any MCP client) | 2025-2026 | MCP server can be used from any MCP-compatible agent, not just Claude Desktop |
| Gamma API beta (limited access) | Gamma API v1.0 GA | Nov 5, 2025 | API is now generally available to all Pro+ accounts with generous credit limits |
| Custom slide generation (python-pptx) | Gamma AI-designed presentations | 2024-2025 | AI-generated layouts eliminate manual design work; trade-off is less pixel-precise control |
| GHL webhook direct to local machine | n8n webhook relay pattern | Current | n8n handles event buffering, pre-processing, and already has a reachable endpoint |
| Manual proposal creation | Agent-assisted with HITL gates | Phase 5 | Agent handles analysis and generation; operator retains approval authority |

**Deprecated/outdated:**
- Gamma API v0.x beta endpoints: Replaced by v1.0 GA. Use current API parameters per developers.gamma.app/docs.
- `get_themes` and `get_folders` tool names from older MCP versions: Current tools are `gamma_list_themes` and `gamma_list_folders` in the `@purple-horizons/gamma-mcp` package.

## Open Questions

1. **Gamma Account Tier and Credits**
   - What we know: Gamma requires Pro ($16/mo) or higher for API access. Credits cost ~1-5 per card, 2-125 per image. A 12-slide deck with basic AI images costs ~20-60 credits.
   - What's unclear: How many monthly credits come with the Pro plan. Whether auto-recharge is available. What happens to in-progress generations when credits run out.
   - Recommendation: Sign up for Gamma Pro, generate the API key, and test credit consumption with a sample deck before planning relies on specific credit budgets. STATE.md already flags: "Gamma MCP access is gated -- must confirm API access before planning Phase 5."

2. **GHL Webhook Relay via n8n**
   - What we know: n8n is running in the Docker stack (Phase 1). GHL can fire webhooks to n8n. n8n can relay to a local OpenClaw endpoint. The `OpportunityStageUpdate` webhook payload includes contactId, pipelineStageId, and monetary value.
   - What's unclear: Whether GHL webhooks are already configured to point to n8n. Whether n8n has a publicly reachable URL or needs Tailscale Funnel. The exact pipeline stage IDs for the "qualified" stage in the operator's GHL account.
   - Recommendation: During setup, configure the GHL webhook pointing to n8n, set up the relay workflow, and query GHL for pipeline stage IDs. Store the "qualified" stage ID as an environment variable.

3. **Discovery Form Delivery Mechanism**
   - What we know: GHL has a native form/survey builder but no programmatic API for creating forms. The agent generates discovery questions; the operator needs to send them to the prospect.
   - What's unclear: Whether to use GHL native forms (operator creates manually), a simple hosted HTML form, or Gamma's document format (generate a form-like page as a Gamma document).
   - Recommendation: Start with the simplest approach: agent generates the question set and sends it to the operator via Telegram. Operator creates the GHL survey using the questions and sends the link. Discovery form responses come back via GHL's `FormSubmission` webhook. In a future iteration, consider using Jotform MCP (available in the tool registry) for programmatic form creation.

4. **GHL MCP Server Tool Availability**
   - What we know: A GHL MCP server exists on the Windows machine (`GoHighLevel-MCP`). It supports contact and opportunity operations. The exact tool list is unaudited.
   - What's unclear: Whether the GHL MCP server exposes `get_contact`, `get_opportunity`, and `search_opportunities` tools. Whether it handles custom field retrieval (needed for `industry`, `pain_signals`, `tech_stack`).
   - Recommendation: Audit the GHL MCP server tools before Phase 5 planning. If contact custom fields aren't available, use the n8n GHL proxy (Phase 1) to fetch enriched contact data via REST API.

5. **Client Knowledge Base for PROP-06**
   - What we know: Per-Task RAG (Phase 6) will provide dedicated collections. Phase 2 provides hybrid search (FTS5 + Qdrant) on the memory system.
   - What's unclear: How much industry-specific content is indexed in the current memory system. Whether the existing Qdrant collection has enough domain knowledge for meaningful pitch deck context.
   - Recommendation: Before Phase 5 implementation, seed the memory system with industry pain point documents, case studies, and service descriptions for target verticals (plumbing, solar, dental, legal). This provides the knowledge base for PROP-06 even without Phase 6's full per-task RAG.

## Integration Points with Existing Code

### Transcript Extraction (Phase 4, 04-01)
- **Reuse:** `extractFromTranscript()` from `src/transcripts/extractor.ts` provides the LLM extraction pipeline.
- **Extend:** Proposal analysis uses a different prompt but the same extraction pattern (call routeAndCall, parse JSON, strip code fences).
- **New module:** `src/proposals/analyzer.ts` wraps the extraction with proposal-specific prompt and output types.

### HITL Approval Queue (Phase 3, 03-01)
- **Reuse:** `requestApproval()`, `updateApprovalStatus()`, `getPendingApproval()` from `src/hitl/approval-queue.ts`.
- **Extend:** Register new callback patterns `proposal:approve:*`, `proposal:edit:*`, `proposal:reject:*` in a new callback handler alongside existing `approve:*`, `reject:*`.
- **Classification:** Proposal delivery classified as RED tier in `classify.ts` (external communication, reputation-affecting).

### Telegram Bot (Phase 3, 03-01)
- **Reuse:** `bot.api.sendMessage()` for proposal preview messages. `InlineKeyboard` for Approve/Edit/Reject buttons.
- **New commands:** `/proposal {prospect}` to manually trigger proposal generation. `/proposal-status` to check pending proposals.
- **Formatting:** Use `escapeMarkdownV2()` from `src/telegram/formatters.ts` for all proposal messages.

### Model Router (Phase 2, 02-02)
- **Routing:** Proposal analysis and discovery form generation route to Sonnet tier (client-facing quality per MODL-01). CRM-triggered deck content assembly uses Sonnet. Theme selection logic uses Haiku (simple matching task).

### Memory/Search (Phase 2, 02-01)
- **Industry context:** Use `hybridSearch()` or direct Qdrant search for industry pain points, case studies, and competitive context. Provides the "client knowledge RAG" for PROP-06 until Phase 6 delivers dedicated collections.

### Notion Action Log (Phase 3, 03-03)
- **Logging:** Log all proposal lifecycle events (created, discovery sent, generated, approved, delivered, rejected) to the Notion action log via `logAction()`.

### n8n Proxy (Phase 1, 01-02)
- **GHL data:** Use the n8n GHL proxy to fetch contact data if GHL MCP tools don't provide custom fields. Proxy handles API key security (SECR-01).

## Sources

### Primary (HIGH confidence)
- [Gamma Generate API Parameters](https://developers.gamma.app/docs/generate-api-parameters-explained) - Full parameter reference, textMode, imageOptions, cardOptions, sharingOptions
- [Gamma API Access and Pricing](https://developers.gamma.app/docs/get-access) - Credit system, tier requirements, API key generation
- [Gamma Create from Template API](https://developers.gamma.app/docs/create-from-template-parameters-explained) - Template-based generation with gammaId, prompt, theme override
- [Purple-Horizons/gamma-mcp GitHub](https://github.com/Purple-Horizons/gamma-mcp) - MCP server implementation, 5 tools, npm package, MIT license
- [GHL OpportunityStageUpdate Webhook](https://marketplace.gohighlevel.com/docs/webhook/OpportunityStageUpdate/index.html) - Webhook payload structure with all fields and sample payload
- Phase 3 plans (03-01) - HITL approval queue, Telegram bot, inline keyboards
- Phase 4 plans (04-01) - Transcript extraction pipeline, LLM structured extraction
- Phase 2 plans (02-01, 02-02) - Memory hybrid search, model router with tier routing

### Secondary (MEDIUM confidence)
- [Gamma MCP Server Official Docs](https://developers.gamma.app/docs/gamma-mcp-server) - MCP connector setup, authentication flow
- [GHL Webhook Integration Guide](https://marketplace.gohighlevel.com/docs/webhook/WebhookIntegrationGuide/index.html) - Webhook registration, event types
- [n8n HighLevel Integration](https://n8n.io/integrations/webhook/and/highlevel/) - n8n + GHL webhook relay patterns
- Blueprint: `08-Capabilities-Deep-Dive/presentations/gamma-mcp-integration.md` - Trigger design, theme selection, HITL flow, error handling
- Blueprint: `05-Skills-Development/priority-skills/gamma-presentation-skill.md` - Skill definition, execution flow, metrics
- Blueprint: `08-Capabilities-Deep-Dive/presentations/templates.md` - Template categories (pitch deck, monthly report, strategy proposal), placeholder system
- Blueprint: `08-Capabilities-Deep-Dive/crm-management/pipeline-automation.md` - Pipeline stages, automated transitions, stage definitions
- Blueprint: `06-Integrations/gohighlevel/webhook-setup.md` - Webhook URL options, event-to-action mapping, security

### Tertiary (LOW confidence)
- GHL programmatic form/survey creation API: Not found in documentation. GHL forms are created via dashboard UI. Needs validation that `FormSubmission` webhook fires for survey responses.
- Gamma credit costs per card/image at different tiers: Ranges provided (1-5 per card, 2-125 per image) but exact Pro tier monthly allocation not confirmed. Needs validation with actual account.
- GHL MCP server tool inventory: Not audited. Tool availability for custom field retrieval is assumed but not verified.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Gamma MCP server verified against official docs with 5 tools documented. All other libraries already installed from Phases 1-4. No new npm dependencies beyond gamma-mcp.
- Architecture: HIGH - Proposal pipeline follows established patterns: LLM extraction (Phase 4), HITL approval (Phase 3), webhook listener (n8n relay from Phase 1), SQLite state tracking (Phases 1-4).
- Gamma integration: HIGH - API v1.0 is GA, MCP server is MIT licensed with documented tools, parameters match official Generate API docs.
- GHL CRM triggers: MEDIUM - OpportunityStageUpdate webhook payload is documented, but the n8n relay configuration and pipeline stage ID retrieval require setup verification.
- Discovery forms: MEDIUM - LLM generation of form content is straightforward, but the delivery mechanism (GHL native forms vs hosted form) needs operator preference input.
- Client knowledge RAG: MEDIUM - Phase 2 hybrid search is available as a substitute for Phase 6 per-task RAG, but the quality of industry context depends on seeded content.
- Pitfalls: HIGH - Gamma credit management, webhook deduplication, proposal quality control, and HITL enforcement are well-understood risks with clear mitigations documented above.

**Research date:** 2026-03-02
**Valid until:** 2026-04-01 (Gamma API is GA and stable; monitor for GHL webhook format changes)

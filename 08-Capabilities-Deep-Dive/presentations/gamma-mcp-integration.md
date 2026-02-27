# Gamma MCP Integration for Autonomous Presentation Creation

> **Status:** Research | **Last Updated:** 2026-02-26
> **Depends on:** [Templates](templates.md), [Telegram Bot](../../07-Channel-Setup/telegram-bot.md), [HITL](../../02-Security/human-in-the-loop.md)

---

## 1. What This Is

Gamma is an AI-powered presentation platform that generates professional slides from text prompts. OpenClaw integrates with Gamma through its MCP (Model Context Protocol) server, enabling autonomous presentation creation triggered by events like new qualified leads, monthly report dates, or user requests.

**Why Gamma vs python-pptx vs Google Slides:**

| Method | Strengths | Weaknesses | Best For |
|--------|-----------|------------|----------|
| **Gamma MCP** | AI-designed layouts, beautiful themes, web-hosted, PPTX/PDF export | Less template control, depends on external service | Client-facing decks, quick turnaround |
| **python-pptx** | Full template control, offline, free | Manual layout work, requires design skills | Internal reports, template-locked decks |
| **Google Slides API** | Free, collaborative editing, programmatic | Limited design capability, needs Google Workspace | Collaborative drafts, simple slides |

**Decision matrix:** Use Gamma for client-facing presentations where design quality matters. Use python-pptx for templated reports with strict branding. Use Google Slides for collaborative internal decks.

---

## 2. Gamma MCP Tools

The Gamma MCP server exposes these tools to OpenClaw:

### 2.1 `generate`

Creates a new presentation, document, webpage, or social media post.

**Key parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `inputText` | Yes | The content/outline for the presentation |
| `format` | No | `presentation` (default), `document`, `social`, `webpage` |
| `numCards` | No | Number of slides (Gamma has intelligent defaults) |
| `textMode` | No | `generate` (expand brief prompts), `condense` (summarize long content), `preserve` (use as-is) |
| `themeId` | No | Theme ID from `get_themes` |
| `exportAs` | No | `pptx` or `pdf` (only when export needed) |
| `cardOptions.dimensions` | No | `16x9` (default), `4x3`, `fluid`, etc. |
| `textOptions.amount` | No | `brief`, `medium`, `detailed`, `extensive` |
| `textOptions.tone` | No | `professional`, `casual`, etc. |
| `textOptions.language` | No | Language code (e.g., `en`) |
| `imageOptions.source` | No | `aiGenerated` (default), `webAllImages`, `pexels`, `noImages` |

**Return value:** A `generationId` for status polling and a `gammaUrl` when complete.

### 2.2 `get_generation_status`

Checks if a generation is still in progress or complete.

```
Input: { "generationId": "abc123" }
Output: { "status": "complete", "gammaUrl": "https://gamma.app/docs/..." }
```

### 2.3 `get_themes`

Lists available Gamma themes for matching client branding.

### 2.4 `get_folders`

Lists Gamma folders for organizing generated content.

---

## 3. MCP Server Registration

Register the Gamma MCP server in OpenClaw's tool registry:

```yaml
# In OpenClaw MCP configuration
mcp_servers:
  gamma:
    name: "Gamma"
    description: "AI-powered presentation and document generation"
    tools:
      - generate
      - get_generation_status
      - get_themes
      - get_folders
    auth:
      type: api_key
      key_env: GAMMA_API_KEY
    rate_limits:
      max_requests_per_minute: 10
      max_concurrent: 2
```

---

## 4. Authentication and Pricing

### 4.1 Authentication

Gamma MCP uses API key authentication. The key is associated with your Gamma account and determines access level.

**Setup:**
1. Sign up at gamma.app
2. Generate an API key from account settings
3. Store in credential manager: `GAMMA_API_KEY`

### 4.2 Pricing Considerations

Gamma offers free and paid tiers:

| Tier | Generations | AI Images | Export |
|------|------------|-----------|--------|
| Free | Limited/month | Limited | Watermarked |
| Plus (~$10/mo) | Unlimited | Unlimited AI images | PPTX/PDF without watermark |
| Pro (~$20/mo) | Unlimited | Premium AI models | Full export, custom branding |

**Recommendation:** Start with Plus tier ($10/mo). Upgrade to Pro if generating client-facing decks frequently (watermark removal and custom branding are critical for professional delivery).

**Cost impact on monthly budget:**
- Add $10-20/mo to the API costs documented in [api-costs.md](../../10-Cost-Analysis/api-costs.md)

---

## 5. Trigger Design

### 5.1 Event-Driven Triggers

| Trigger | When | What to Generate |
|---------|------|-----------------|
| CRM stage change | Lead moves to "qualified" or "proposal_sent" | Pitch deck tailored to lead's industry |
| Monthly date | 1st or last business day of month | Monthly performance report for each active client |
| User request via Telegram | User says "create a deck for [client]" | Specified presentation type |
| New competitor data | Competitor monitoring detects changes | Updated competitor analysis deck |
| Campaign completion | Ad campaign reaches end date | Campaign performance summary |

### 5.2 CRM-Triggered Generation

```python
async def on_pipeline_stage_change(event):
    """Trigger when a GHL opportunity changes stage."""
    if event.new_stage == "qualified":
        lead = await ghl.get_contact(event.contact_id)
        industry_data = await memory.search(f"{lead.industry} pain points")

        # Generate pitch deck via Gamma
        generation = await gamma.generate(
            inputText=f"""Create a pitch deck for {lead.company_name}.
            Industry: {lead.industry}
            Pain points: {industry_data.top_results}
            Services to highlight: SEO, PPC, Social Media
            Include case study from similar industry client.""",
            format="presentation",
            numCards=12,
            textOptions={"tone": "professional", "amount": "medium"},
            imageOptions={"source": "aiGenerated", "style": "professional photography"},
        )

        # Post preview to Telegram for approval
        await telegram.send_message(
            chat_id=USER_TELEGRAM_ID,
            text=f"Generated pitch deck for {lead.company_name}.\n"
                 f"Preview: {generation.gammaUrl}\n"
                 f"Approve to send to lead?",
            reply_markup=approval_keyboard(generation.id)
        )
```

### 5.3 Scheduled Monthly Reports

```yaml
# LaunchAgent or cron trigger
triggers:
  - type: cron
    schedule: "0 9 1 * *"  # 9 AM on 1st of each month
    action: generate_monthly_reports
```

```python
async def generate_monthly_reports():
    """Generate monthly report for every active client."""
    active_clients = await ghl.list_locations(status="active")

    for client in active_clients:
        data = await assemble_report_data(client, period="last_month")

        generation = await gamma.generate(
            inputText=format_monthly_report_outline(client, data),
            format="presentation",
            numCards=14,
            textMode="generate",
            textOptions={"tone": "professional", "amount": "detailed"},
            exportAs="pdf",  # Also export PDF for email delivery
        )

        await telegram.send_message(
            chat_id=USER_TELEGRAM_ID,
            text=f"Monthly report for {client.name} ready.\n"
                 f"Preview: {generation.gammaUrl}\n"
                 f"[Approve & Send] [Edit First] [Skip]",
            reply_markup=report_approval_keyboard(generation.id, client.id)
        )
```

---

## 6. Theme Selection Logic

Map client branding keywords to Gamma themes:

```python
async def select_gamma_theme(client_brand: dict) -> str:
    """Select the best Gamma theme based on client branding."""
    themes = await gamma.get_themes()

    # Build scoring criteria from client brand
    style = client_brand.get("style", "professional")
    primary_color = client_brand.get("colors", {}).get("primary", "#1B4D89")

    # Score each theme
    scored_themes = []
    for theme in themes:
        score = 0
        if style.lower() in theme.get("tone", "").lower():
            score += 3
        if similar_color(primary_color, theme.get("primary_color")):
            score += 2
        if theme.get("category") == "business":
            score += 1
        scored_themes.append((theme, score))

    # Return best match, or None for Gamma's default
    best = max(scored_themes, key=lambda x: x[1])
    return best[0]["id"] if best[1] > 2 else None
```

---

## 7. HITL Flow

All Gamma-generated presentations follow this approval flow:

```
Event triggers generation
    |
    v
Agent generates presentation via Gamma MCP
    |
    v
Agent posts preview link to Telegram
    |
    v
User reviews in browser (Gamma live preview)
    |
    v
User approves / requests edits / rejects
    |
    v
If approved:
    - Export as PPTX/PDF
    - Deliver to client (email, GHL, direct link)
    - Log in session history
If edit requested:
    - User edits directly in Gamma editor
    - Notifies agent when done
If rejected:
    - Log rejection reason
    - Carry forward for next attempt
```

**Critical:** No presentation is delivered to a client without user approval. This is a Tier 1 HITL action per [human-in-the-loop.md](../../02-Security/human-in-the-loop.md).

---

## 8. Export and Delivery

### 8.1 Export Formats

| Format | Use Case | How |
|--------|----------|-----|
| **Gamma Link** | Quick sharing, live editing | Share the `gammaUrl` directly |
| **PPTX** | Client wants editable file | Set `exportAs: "pptx"` in generate call |
| **PDF** | Email attachment, formal delivery | Set `exportAs: "pdf"` in generate call |

### 8.2 Delivery Channels

After user approval:
- **Email via GHL:** Attach PDF or include Gamma link in email template
- **Telegram:** Send download link to user for manual forwarding
- **Direct link:** Share Gamma URL for client to view in browser

---

## 9. Error Handling

| Error | Response |
|-------|----------|
| Generation times out (> 5 min) | Notify user, retry once, then escalate |
| Gamma API rate limit | Queue and retry with exponential backoff |
| Theme not found | Fall back to Gamma's default theme |
| Export fails | Provide Gamma link as fallback, retry export |
| Content too long for slide count | Increase `numCards` or switch to `condense` mode |

---

## 10. Research Gaps

- [ ] Confirm exact Gamma API rate limits for Plus/Pro tiers
- [ ] Test bulk generation (5+ decks in sequence) for monthly report batches
- [ ] Benchmark generation time for 12-slide vs 14-slide decks
- [ ] Evaluate Gamma's custom font support for strict client branding
- [ ] Test PPTX export quality for offline editing compatibility

---

## Next Steps

- [Gamma Presentation Skill](../../05-Skills-Development/priority-skills/gamma-presentation-skill.md) -- OpenClaw skill definition
- [Templates](templates.md) -- template system (python-pptx path)
- [API Costs](../../10-Cost-Analysis/api-costs.md) -- updated cost projections

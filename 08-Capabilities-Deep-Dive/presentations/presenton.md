# Presenton: Open-Source AI Presentation Tool

## Overview

Presenton is an open-source AI-powered presentation generation tool that converts text prompts and content descriptions into polished slide decks. Unlike python-pptx (which requires explicit programming of every element) or the Google Slides API (which requires explicit API calls), Presenton uses AI to automatically structure content, choose layouts, and generate visually appealing slides from high-level input.

**RESEARCH GAP:** The details below are based on initial research and may need verification. The project's current state, API availability, self-hosting requirements, and exact feature set should be confirmed before relying on this tool in production.

## Project Information

- **GitHub Repository:** presenton/presenton (verify current URL and activity)
- **License:** Open-source (verify specific license)
- **Status:** Active development (verify current release status)
- **Technology Stack:** Likely Python/TypeScript with AI model integration

## How It Works

The general flow for AI presentation generators like Presenton:

```
User Input (text prompt, document, URL)
    -> AI Content Structuring (outline, key points, slide breakdown)
        -> Layout Selection (AI picks appropriate slide templates)
            -> Content Generation (text, bullet points, headings per slide)
                -> Design Application (theme, colors, fonts, spacing)
                    -> Export (PPTX, PDF, Google Slides, or web format)
```

### Input Methods (Expected)

1. **Text Prompt:** "Create a 10-slide pitch deck for a digital marketing agency targeting local service businesses"
2. **Document Upload:** Feed a strategy document, and the AI extracts key points into slides
3. **URL Input:** Provide a blog post or report URL, AI summarizes into presentation
4. **Structured JSON:** Provide outline with specific content per slide

### Output Formats (Expected)

- PowerPoint (.pptx)
- PDF
- Possibly Google Slides export
- Web-based preview/presentation

## Self-Hosting with Docker

If Presenton supports Docker deployment (common for open-source tools):

```yaml
# docker-compose.yml (hypothetical - verify actual requirements)
version: '3.8'
services:
  presenton:
    image: presenton/presenton:latest  # verify actual image name
    ports:
      - "3200:3000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}  # likely requires LLM API key
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}  # possibly supports multiple providers
    volumes:
      - ./presenton-data:/app/data
      - ./templates:/app/templates
    restart: unless-stopped
```

### Mac Mini Deployment Considerations

- **Resources:** AI presentation generation can be CPU/memory intensive during rendering
- **Storage:** Template library and generated presentations need disk space
- **GPU:** Not typically required (AI calls go to external LLM APIs)
- **Network:** Needs outbound access to LLM APIs (OpenAI, Anthropic, etc.)

## Design Quality

AI presentation tools generally produce:

- **Modern layouts:** Clean, minimalist designs with proper whitespace
- **Consistent styling:** Uniform fonts, colors, and spacing throughout
- **Smart content distribution:** AI decides how much content fits per slide
- **Visual hierarchy:** Proper heading sizes, bullet point indentation
- **Image placement:** AI suggests or generates relevant imagery (if supported)

### Quality Compared to Manual Design

| Aspect            | AI-Generated        | Professionally Designed   |
|-------------------|---------------------|---------------------------|
| Speed             | Seconds to minutes  | Hours to days              |
| Consistency       | Very consistent     | Varies by designer         |
| Creativity        | Template-bound      | Highly creative            |
| Brand accuracy    | Needs configuration | Pixel-perfect              |
| Data visualization| Basic               | Advanced and custom        |
| Overall polish    | 7/10                | 9-10/10                    |

## Customization Options (Expected)

- **Themes:** Pre-built color schemes and layout collections
- **Colors:** Primary, secondary, accent color customization
- **Fonts:** Heading and body font selection
- **Layout Preferences:** Minimal text, data-heavy, image-focused
- **Aspect Ratio:** 16:9 (standard), 4:3 (legacy), custom
- **Slide Count:** Target number of slides
- **Content Density:** Brief (3-5 words per bullet) vs. detailed (full sentences)

## API Access for OpenClaw Integration

If Presenton exposes a REST API:

```python
# Hypothetical API integration
import httpx

async def generate_presentation_with_presenton(prompt: str, options: dict) -> str:
    """
    Generate a presentation using Presenton's API.
    Returns: URL or file path to generated presentation.
    """
    response = await httpx.post(
        "http://localhost:3200/api/generate",  # verify actual endpoint
        json={
            "prompt": prompt,
            "theme": options.get("theme", "professional"),
            "colors": {
                "primary": options.get("primary_color", "#1A1A2E"),
                "accent": options.get("accent_color", "#007BFF")
            },
            "slides": options.get("slide_count", 10),
            "format": options.get("format", "pptx"),
            "aspect_ratio": "16:9"
        },
        timeout=120.0  # generation can take time
    )

    result = response.json()
    return result["download_url"]  # or file path
```

### Integration as OpenClaw Skill

```python
# Skill: quick_presentation
# Uses Presenton for fast draft generation

async def quick_presentation(request: str, client_context: dict) -> dict:
    """
    Generate a quick draft presentation using AI.

    Steps:
    1. Build prompt from request + client context
    2. Call Presenton API to generate draft
    3. Optionally refine with python-pptx (branding, specific data)
    4. Return download link or file path
    """
    prompt = f"""
    Create a presentation for {client_context['client_name']},
    a {client_context['industry']} business.

    Request: {request}

    Include their brand colors: {client_context['brand_colors']}
    Tone: Professional, data-driven, actionable
    """

    draft_url = await generate_presentation_with_presenton(
        prompt=prompt,
        options={
            "theme": "corporate",
            "primary_color": client_context['brand_colors']['primary'],
            "slide_count": 12
        }
    )

    return {
        "status": "success",
        "draft_url": draft_url,
        "note": "This is an AI-generated draft. Review and refine before sending to client."
    }
```

## Comparison with Other Approaches

| Feature            | Presenton (AI)         | python-pptx            | Google Slides API       |
|--------------------|------------------------|------------------------|------------------------|
| Input              | Natural language       | Python code            | API calls              |
| Design automation  | Full (AI-driven)       | None (manual)          | None (manual)          |
| Content generation | AI writes content      | Must provide content   | Must provide content   |
| Customization      | Theme-level            | Pixel-level            | Element-level          |
| Data integration   | Limited                | Full programmatic      | Full programmatic      |
| Template system    | Built-in AI templates  | Custom .pptx templates | Custom GSlides templates |
| Branding control   | Color/font settings    | Complete control       | Good control           |
| Speed to first draft| Fastest               | Moderate               | Moderate               |
| Reliability        | Varies (AI output)     | Deterministic          | Deterministic          |
| Self-hostable      | Yes (if Docker)        | N/A (library)          | No (Google service)    |

## Recommended Usage in OpenClaw

### Tiered Approach

1. **Quick Draft (Presenton):** When the user says "make me a presentation about X" with minimal specifics, use Presenton for a fast first draft
2. **Data-Driven Report (python-pptx):** When the presentation needs specific CRM data, charts from analytics, and precise formatting, use python-pptx with templates
3. **Collaborative Delivery (Google Slides):** When the presentation needs to be shared as a link, commented on, or edited collaboratively, use Google Slides API
4. **Hybrid Flow:** Generate draft with Presenton, refine data slides with python-pptx, upload to Google Slides for sharing

### Decision Matrix

```
User says "create a quick presentation" -> Presenton
User says "generate the monthly report" -> python-pptx (templated, data-driven)
User says "prepare a pitch deck for the client meeting" -> Presenton draft -> python-pptx refinement
User says "share the report with the client" -> Google Slides API
```

## Items Requiring Verification

Before integrating Presenton into OpenClaw, confirm:

- [ ] Current GitHub repository URL and activity status
- [ ] Available API endpoints and documentation
- [ ] Docker image availability and deployment requirements
- [ ] Supported LLM backends (OpenAI, Anthropic, local models)
- [ ] Export format support (PPTX, PDF, Google Slides)
- [ ] Template customization capabilities
- [ ] Branding control (logo injection, color schemes)
- [ ] Performance benchmarks (time to generate 15-slide deck)
- [ ] Stability and production-readiness
- [ ] Community activity and maintenance frequency
- [ ] Licensing terms for commercial use
- [ ] Cost of LLM API calls per presentation generated

## Alternative Open-Source AI Presentation Tools

If Presenton does not meet requirements, evaluate these alternatives:

- **SliDev:** Markdown-based presentation tool (developer-focused)
- **Marp:** Markdown to presentation converter with themes
- **Reveal.js:** HTML presentation framework (web-based output)
- **Gamma.app:** AI presentation tool (SaaS, not self-hosted)
- **Custom Solution:** Use Claude/GPT to generate structured JSON, then feed to python-pptx

## References

- Presenton GitHub: https://github.com/presenton/presenton (verify)
- Comparison of presentation tools: research current landscape

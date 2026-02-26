# Presentation Generation Skill

## Goal

Build an OpenClaw skill that generates professional, polished presentations on demand. The agent should be able to take a topic, audience description, and key points, then produce a fully designed PowerPoint or PDF presentation ready for client delivery.

---

## Approach Comparison

### 1. Python-PPTX (Recommended)

**What it is**: Python library for programmatic PowerPoint (.pptx) creation and manipulation.

**Pros**:
- Full control over every element: slides, shapes, text, images, charts, tables
- No external API dependency -- runs entirely locally
- Free and open source (MIT license)
- Can use existing .pptx templates as a starting point
- Handles complex layouts: multi-column, nested shapes, custom positioning
- Excellent chart support via python-pptx's chart module

**Cons**:
- Requires Python runtime (OpenClaw skill would shell out to Python or use a Python execution environment)
- Design quality depends on template quality and positioning logic
- No built-in AI design capabilities -- you must define layouts programmatically
- Learning curve for complex layouts

**Implementation Path**:
```
OpenClaw Skill (TypeScript)
  -> Generates slide content/structure (JSON)
  -> Calls Python script with python-pptx
  -> Python script creates .pptx from template + content JSON
  -> Returns .pptx file path
```

### 2. Google Slides API

**What it is**: REST API for creating and modifying Google Slides presentations.

**Pros**:
- Cloud-based -- no local rendering needed
- Collaborative: clients can edit the result in Google Slides
- Good API for text, images, charts, layouts
- Integration with Google Workspace (Sheets for charts, Drive for storage)

**Cons**:
- Requires Google Cloud project and OAuth setup
- API is verbose -- many API calls for a single presentation
- Less control over pixel-perfect positioning compared to python-pptx
- Rate limits (read: 300/min, write: 60/min per project)
- Output is in Google Slides format (export to .pptx is lossy)

### 3. Presenton (Open-Source AI Presentation Tool)

**What it is**: Open-source tool that uses AI to generate presentations.

**Pros**:
- AI-native: designed for LLM-generated content
- Can be self-hosted
- Handles design decisions automatically

**Cons**:
- Less mature than python-pptx
- May have limited customization options
- Need to evaluate current feature set and stability
- **RESEARCH GAP**: Need to evaluate Presenton's current capabilities, stability, and self-hosting requirements

### 4. Marp (Markdown to Presentation)

**What it is**: Converts Markdown documents to presentation slides (HTML, PDF, PPTX).

**Pros**:
- Extremely simple: write Markdown, get slides
- Fast generation
- Good for internal/technical presentations
- CLI tool: `marp --pptx input.md`

**Cons**:
- Limited design capabilities (theme-based, not custom layout)
- Not suitable for polished client-facing presentations
- Limited chart/graph support
- No complex multi-column layouts

### Recommendation

**Primary**: Python-PPTX for maximum flexibility and professional output quality.
**Secondary**: Marp for quick internal presentations where design is less critical.

---

## Skill Design: @yourname/presentation-generator

### skill.json Manifest (Key Sections)

```json
{
  "name": "@yourname/presentation-generator",
  "version": "1.0.0",
  "description": "Generate professional PowerPoint presentations from topic and key points",
  "commands": ["/presentation", "/slides", "/pptx"],
  "inputs": {
    "required": {
      "topic": {
        "type": "string",
        "description": "Presentation topic or title"
      },
      "audience": {
        "type": "string",
        "description": "Who the presentation is for (e.g., 'small business owners', 'marketing team')"
      }
    },
    "optional": {
      "key_points": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Main points to cover"
      },
      "num_slides": {
        "type": "integer",
        "default": 10,
        "minimum": 3,
        "maximum": 30,
        "description": "Target number of slides"
      },
      "style": {
        "type": "string",
        "enum": ["professional", "modern", "minimal", "bold", "corporate"],
        "default": "professional"
      },
      "template": {
        "type": "string",
        "description": "Name of pre-designed template to use"
      },
      "brand": {
        "type": "object",
        "properties": {
          "primary_color": { "type": "string", "description": "Hex color code" },
          "secondary_color": { "type": "string" },
          "logo_path": { "type": "string" },
          "font_heading": { "type": "string" },
          "font_body": { "type": "string" },
          "company_name": { "type": "string" }
        },
        "description": "Brand customization"
      },
      "include_charts": {
        "type": "boolean",
        "default": false,
        "description": "Whether to include data visualization charts"
      },
      "chart_data": {
        "type": "object",
        "description": "Data for charts (keys: chart title, values: data arrays)"
      },
      "output_format": {
        "type": "string",
        "enum": ["pptx", "pdf", "both"],
        "default": "pptx"
      }
    }
  },
  "outputs": {
    "file_path": { "type": "string", "description": "Path to generated presentation file" },
    "slide_count": { "type": "integer" },
    "outline": { "type": "array", "description": "Slide titles and summaries" }
  },
  "tools": {
    "required": ["code_execution", "file_write"],
    "optional": ["web_fetch", "file_read"]
  },
  "permissions": {
    "filesystem": ["read:./templates", "write:./output"],
    "system": ["shell:python3"]
  },
  "dependencies": {
    "npm": { "zod": "^3.22.0" }
  }
}
```

### Execution Flow

```
Step 1: Generate Outline
  Input: topic, audience, key_points, num_slides
  Process: LLM generates structured slide outline
  Output: Array of { title, bullet_points, slide_type, notes }

Step 2: Generate Content
  Input: outline + audience context
  Process: LLM generates detailed content for each slide
  Output: Array of { title, subtitle, body_text, speaker_notes, image_suggestion }

Step 3: Select/Apply Template
  Input: style, brand, template name
  Process: Load .pptx template, apply brand colors/fonts/logo
  Output: Configured template object

Step 4: Build Slides
  Input: content array + configured template
  Process: Python-PPTX creates each slide with:
    - Title and subtitle
    - Body text with proper formatting
    - Bullet points
    - Charts/graphs (if include_charts)
    - Images (if available)
    - Speaker notes
  Output: .pptx file

Step 5: Export
  Input: .pptx file + output_format
  Process: If PDF requested, convert using LibreOffice CLI or similar
  Output: Final file(s) + metadata
```

### Slide Types

The skill should support these slide types, with different layouts for each:

| Slide Type | Layout | When to Use |
|------------|--------|-------------|
| **Title** | Large centered title + subtitle + optional logo | First slide |
| **Section Header** | Large section name + decorative element | Topic transitions |
| **Content** | Title + bullet points (3-5 bullets) | Main content |
| **Two Column** | Title + two columns of content | Comparisons, before/after |
| **Image + Text** | Title + image on one side, text on other | Visual concepts |
| **Chart** | Title + chart/graph + brief description | Data visualization |
| **Quote** | Large styled quote + attribution | Testimonials, key messages |
| **Stats** | 3-4 large numbers with labels | Key metrics, results |
| **Timeline** | Horizontal or vertical timeline | Process, history |
| **Thank You** | Closing message + contact info | Final slide |

---

## Template System

### Pre-Designed Templates

Create a library of templates organized by use case:

```
templates/
├── industries/
│   ├── home-services.pptx      # Plumber, HVAC, electrician
│   ├── solar-energy.pptx       # Solar installers
│   ├── dental.pptx             # Dental practices
│   ├── legal.pptx              # Law firms
│   ├── real-estate.pptx        # Real estate agents
│   └── general-smb.pptx        # Generic small business
├── purposes/
│   ├── sales-pitch.pptx        # Client pitch decks
│   ├── monthly-report.pptx     # Monthly performance reports
│   ├── strategy-proposal.pptx  # Marketing strategy proposals
│   ├── onboarding.pptx         # Client onboarding presentations
│   └── case-study.pptx         # Case study presentations
└── styles/
    ├── minimal-light.pptx      # Clean, light background
    ├── minimal-dark.pptx       # Clean, dark background
    ├── corporate-blue.pptx     # Traditional corporate
    ├── modern-gradient.pptx    # Modern with gradient accents
    └── bold-accent.pptx        # Bold colors, strong typography
```

### Template Creation Process

1. Design master templates in PowerPoint with placeholder layouts
2. Define slide masters for each slide type
3. Use placeholder shapes that python-pptx can populate
4. Include brand color slots (primary, secondary, accent) that can be overridden
5. Store templates in the skill's `templates/` directory

---

## Data Visualization

### Chart Types Supported via Python-PPTX + Matplotlib

| Chart Type | Best For | Library |
|------------|----------|---------|
| Bar chart | Comparing categories | python-pptx native |
| Line chart | Trends over time | python-pptx native |
| Pie chart | Composition/percentages | python-pptx native |
| Scatter plot | Correlations | matplotlib -> image |
| Heatmap | Complex comparisons | matplotlib -> image |
| Gauge | Single metrics | matplotlib -> image |
| Funnel | Pipeline/conversion | matplotlib -> image |

### Implementation

For native PowerPoint charts (bar, line, pie):
```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

chart_data = CategoryChartData()
chart_data.categories = ['Q1', 'Q2', 'Q3', 'Q4']
chart_data.add_series('Revenue', (1200, 1500, 1800, 2100))
chart_data.add_series('Target', (1000, 1400, 1700, 2000))

chart = slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED, left, top, width, height, chart_data
).chart
```

For complex charts (heatmap, funnel, gauge):
```python
import matplotlib.pyplot as plt
# Generate chart as image
fig, ax = plt.subplots(figsize=(8, 5))
# ... create chart ...
fig.savefig('chart.png', dpi=150, bbox_inches='tight', transparent=True)
# Then embed image in slide
slide.shapes.add_picture('chart.png', left, top, width, height)
```

---

## Image Integration

### Stock Photo Sources

| Source | Method | Cost |
|--------|--------|------|
| Unsplash API | Free API, attribution required | Free |
| Pexels API | Free API | Free |
| Pixabay API | Free API | Free |
| AI Generation | DALL-E, Midjourney, Stable Diffusion | $0.02-0.10 per image |

### Image Workflow

1. For each slide with `image_suggestion`, the skill:
   a. Searches stock photo API for relevant image
   b. Downloads the best match
   c. Resizes and crops to fit slide layout
   d. Embeds in the presentation with proper positioning
2. If no good stock photo found, optionally generate with AI
3. Always ensure proper attribution for stock photos

---

## Brand Consistency

### Brand Configuration

When a client brand is provided, the skill applies:

```json
{
  "brand": {
    "primary_color": "#1a73e8",
    "secondary_color": "#34a853",
    "accent_color": "#fbbc04",
    "logo_path": "./logos/client-logo.png",
    "font_heading": "Montserrat",
    "font_body": "Open Sans",
    "company_name": "Acme Plumbing Co."
  }
}
```

### What Gets Branded

- Slide background accents use primary/secondary colors
- Title text uses heading font
- Body text uses body font
- Logo appears on title slide and optionally on footer of all slides
- Charts use brand colors for data series
- Section headers use primary color background

---

## Example Usage

### Basic Presentation

```
/presentation
  topic: "Why Your Plumbing Business Needs a Modern Website"
  audience: "Small plumbing business owners in Austin, TX"
  num_slides: 8
  style: professional
```

### Branded Client Pitch

```
/presentation
  topic: "Digital Marketing Strategy for Acme Plumbing"
  audience: "John Smith, owner of Acme Plumbing"
  key_points: [
    "Current online presence analysis",
    "Competitor comparison",
    "Proposed strategy: SEO + Google Ads + Review Management",
    "Expected ROI: 3-5 new leads per week",
    "Investment and timeline"
  ]
  num_slides: 12
  template: "sales-pitch"
  brand: {
    primary_color: "#1a73e8",
    logo_path: "./logos/acme-plumbing.png",
    company_name: "Acme Plumbing Co."
  }
  include_charts: true
  chart_data: {
    "Monthly Lead Projection": { "months": ["Month 1","Month 2","Month 3","Month 4","Month 5","Month 6"], "leads": [2,5,8,12,15,18] },
    "ROI Breakdown": { "categories": ["SEO","Google Ads","Reviews"], "values": [40,35,25] }
  }
```

---

## Dependencies and Setup

### Python Dependencies

```
python-pptx>=0.6.23
matplotlib>=3.8.0
Pillow>=10.0.0
```

### System Dependencies

- Python 3.10+ runtime
- LibreOffice CLI (for PDF conversion): `libreoffice --headless --convert-to pdf`
- Font files for custom fonts (if not system-installed)

### OpenClaw Skill Dependencies

- `@openclaw/code-execution` or shell access for Python scripts
- `@openclaw/file-manager` for output file handling
- Optional: `@yourname/lead-enrichment` for pulling business data into presentations

---

## Quality Checklist

Before delivering any generated presentation:

- [ ] Title slide has correct topic and branding
- [ ] Slide count matches requested or is within reasonable range
- [ ] All text is readable (no overflow, proper font sizes)
- [ ] Charts render correctly with accurate data
- [ ] Images are relevant and properly positioned
- [ ] Brand colors are consistently applied
- [ ] Speaker notes are present and helpful
- [ ] No placeholder text remaining
- [ ] File opens correctly in PowerPoint and Google Slides
- [ ] PDF export (if requested) preserves formatting

---

*Last updated: 2026-02-05*
*Status: Skill design complete; implementation pending OpenClaw access*

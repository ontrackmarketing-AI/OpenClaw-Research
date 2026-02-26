# python-pptx: Programmatic PowerPoint Generation

## Overview

python-pptx is a Python library for creating and updating Microsoft PowerPoint (.pptx) files. It provides full programmatic control over slide creation, content placement, styling, and chart generation without requiring PowerPoint to be installed. For OpenClaw, this is the primary tool for generating offline/downloadable presentation files from structured data.

## Installation

```bash
pip install python-pptx
```

Additional dependencies for image handling:
```bash
pip install Pillow  # for image manipulation before embedding
```

## Core Concepts and Object Hierarchy

```
Presentation (.pptx file)
  -> SlideMaster (defines master layouts)
    -> SlideLayout (title slide, content, blank, etc.)
  -> Slides (individual slides)
    -> Shapes (containers for content)
      -> TextFrame -> Paragraphs -> Runs (text)
      -> Picture (images)
      -> Table (rows and columns)
      -> Chart (bar, line, pie, etc.)
      -> Placeholder (template-defined content areas)
```

## Creating a Presentation from Scratch

### Minimal Example

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

prs = Presentation()

# Title slide
slide_layout = prs.slide_layouts[0]  # 0 = Title Slide layout
slide = prs.slides.add_slide(slide_layout)

title = slide.shapes.title
subtitle = slide.placeholders[1]

title.text = "Monthly Performance Report"
subtitle.text = "Prepared by [Agency Name] - January 2026"

prs.save("report.pptx")
```

### Full Agency Report Example

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE

def create_client_report(client_name, metrics, recommendations):
    prs = Presentation()
    prs.slide_width = Inches(13.333)  # Widescreen 16:9
    prs.slide_height = Inches(7.5)

    # --- Slide 1: Title ---
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = f"{client_name} - Monthly Report"
    slide.placeholders[1].text = "January 2026 Performance Summary"

    # --- Slide 2: Key Metrics ---
    slide = prs.slides.add_slide(prs.slide_layouts[5])  # Blank layout
    # Add title manually
    txBox = slide.shapes.add_textbox(Inches(0.5), Inches(0.3), Inches(12), Inches(1))
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = "Key Performance Metrics"
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0x1A, 0x1A, 0x2E)

    # Add metrics as a table
    rows, cols = len(metrics) + 1, 3
    table_shape = slide.shapes.add_table(rows, cols, Inches(1), Inches(1.5), Inches(11), Inches(4))
    table = table_shape.table

    # Header row
    headers = ["Metric", "Value", "Change"]
    for i, header in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = header
        cell.text_frame.paragraphs[0].font.bold = True
        cell.text_frame.paragraphs[0].font.size = Pt(14)

    # Data rows
    for row_idx, metric in enumerate(metrics, 1):
        table.cell(row_idx, 0).text = metric["name"]
        table.cell(row_idx, 1).text = str(metric["value"])
        table.cell(row_idx, 2).text = metric["change"]

    # --- Slide 3: Chart ---
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    chart_data = CategoryChartData()
    chart_data.categories = ["Week 1", "Week 2", "Week 3", "Week 4"]
    chart_data.add_series("Leads", (12, 18, 24, 31))
    chart_data.add_series("Conversions", (3, 5, 7, 10))

    chart = slide.shapes.add_chart(
        XL_CHART_TYPE.LINE,
        Inches(1), Inches(1.5), Inches(11), Inches(5),
        chart_data
    ).chart
    chart.has_legend = True

    # --- Slide 4: Recommendations ---
    slide = prs.slides.add_slide(prs.slide_layouts[1])  # Title + Content
    slide.shapes.title.text = "Recommendations"
    body = slide.placeholders[1]
    tf = body.text_frame
    tf.clear()
    for rec in recommendations:
        p = tf.add_paragraph()
        p.text = rec
        p.level = 0
        p.font.size = Pt(18)

    prs.save(f"{client_name}_report.pptx")
    return f"{client_name}_report.pptx"
```

## Working with Templates

Templates are the recommended approach for agency work. Design polished templates in PowerPoint, then fill them programmatically.

### Loading and Populating a Template

```python
from pptx import Presentation

def fill_template(template_path, data):
    prs = Presentation(template_path)

    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        for key, value in data.items():
                            placeholder = "{{" + key + "}}"
                            if placeholder in run.text:
                                run.text = run.text.replace(placeholder, str(value))

            # Handle placeholders specifically
            if shape.is_placeholder:
                ph = shape.placeholder_format
                # Map placeholder index to data fields
                # Index 0 = title, 1 = body, etc.

    prs.save("output.pptx")
```

### Placeholder Discovery

```python
# Utility to discover all placeholders in a template
def discover_placeholders(template_path):
    prs = Presentation(template_path)
    for slide_num, slide in enumerate(prs.slides, 1):
        print(f"\n--- Slide {slide_num} ---")
        for shape in slide.shapes:
            if shape.is_placeholder:
                ph = shape.placeholder_format
                print(f"  Placeholder idx={ph.idx}, type={ph.type}, name='{shape.name}'")
            if shape.has_text_frame:
                print(f"  Text: '{shape.text_frame.text[:80]}'")
```

## Slide Layouts Reference

Standard layouts available in the default template (index -> name):

| Index | Layout Name       | Use Case                          |
|-------|-------------------|-----------------------------------|
| 0     | Title Slide       | Cover page, opening slide         |
| 1     | Title and Content  | Main content slides with bullets  |
| 2     | Section Header    | Section dividers                  |
| 3     | Two Content       | Side-by-side comparisons          |
| 4     | Comparison        | Labeled two-column comparison     |
| 5     | Title Only        | Custom content (charts, images)   |
| 6     | Blank             | Fully custom slide                |
| 7     | Content with Caption | Image + description             |
| 8     | Picture with Caption | Large image + caption           |

Custom templates may define additional layouts accessible by index.

## Adding Elements

### Images

```python
# Add image with exact position and size
slide.shapes.add_picture("logo.png", Inches(0.5), Inches(0.3), Inches(2), Inches(1))

# Add image from bytes (useful for dynamically generated charts)
from io import BytesIO
image_stream = BytesIO(image_bytes)
slide.shapes.add_picture(image_stream, Inches(1), Inches(2), Inches(8), Inches(4))
```

### Tables

```python
rows, cols = 5, 4
table_shape = slide.shapes.add_table(rows, cols, Inches(1), Inches(1.5), Inches(10), Inches(4))
table = table_shape.table

# Style cells
for row in table.rows:
    for cell in row.cells:
        cell.text_frame.paragraphs[0].font.size = Pt(12)
        cell.margin_left = Inches(0.1)
        cell.margin_right = Inches(0.1)
```

### Charts

```python
from pptx.chart.data import CategoryChartData, ChartData
from pptx.enum.chart import XL_CHART_TYPE

# Bar Chart
chart_data = CategoryChartData()
chart_data.categories = ["Facebook", "Google", "LinkedIn", "Referral"]
chart_data.add_series("Leads", (45, 62, 18, 23))

slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED,
    Inches(1), Inches(1.5), Inches(10), Inches(5),
    chart_data
)

# Pie Chart
chart_data = CategoryChartData()
chart_data.categories = ["SEO", "PPC", "Social", "Email"]
chart_data.add_series("Budget", (35, 40, 15, 10))

chart_frame = slide.shapes.add_chart(
    XL_CHART_TYPE.PIE,
    Inches(2), Inches(1.5), Inches(8), Inches(5),
    chart_data
)

# Line Chart
chart_data = CategoryChartData()
chart_data.categories = ["Jan", "Feb", "Mar", "Apr", "May"]
chart_data.add_series("Revenue", (12000, 14500, 13800, 16200, 18500))
chart_data.add_series("Cost", (8000, 8500, 8200, 9000, 9500))

slide.shapes.add_chart(
    XL_CHART_TYPE.LINE,
    Inches(1), Inches(1.5), Inches(10), Inches(5),
    chart_data
)
```

## Styling

### Font and Color Control

```python
from pptx.dml.color import RGBColor
from pptx.util import Pt
from pptx.enum.text import PP_ALIGN

# Agency brand colors (example)
BRAND_PRIMARY = RGBColor(0x1A, 0x1A, 0x2E)    # Dark navy
BRAND_ACCENT = RGBColor(0x00, 0x7B, 0xFF)      # Bright blue
BRAND_SUCCESS = RGBColor(0x28, 0xA7, 0x45)     # Green
BRAND_WARNING = RGBColor(0xFF, 0xC1, 0x07)     # Yellow
BRAND_DANGER = RGBColor(0xDC, 0x35, 0x45)      # Red

# Apply to text
run.font.size = Pt(24)
run.font.bold = True
run.font.color.rgb = BRAND_PRIMARY
run.font.name = "Calibri"

# Paragraph alignment
paragraph.alignment = PP_ALIGN.CENTER

# Slide background
from pptx.oxml.ns import qn
background = slide.background
fill = background.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0xF5, 0xF5, 0xF5)
```

## Integration with OpenClaw

### As a Python Skill

The presentation generation system should be implemented as an OpenClaw Python skill:

```python
# Skill: generate_presentation
# Input: structured JSON with presentation specification
# Output: file path to generated .pptx

async def generate_presentation(spec: dict) -> str:
    """
    spec = {
        "type": "client_report",         # template type
        "client": "ABC Plumbing",         # client name
        "template": "monthly_report",     # template file name
        "data": {                         # dynamic data
            "metrics": [...],
            "charts": [...],
            "recommendations": [...]
        },
        "branding": {                     # client branding
            "primary_color": "#1A1A2E",
            "logo_path": "/assets/logos/abc_plumbing.png",
            "font": "Montserrat"
        }
    }
    """
    template_path = f"/openclaw/assets/templates/{spec['template']}.pptx"
    prs = Presentation(template_path)
    # ... populate template with data ...
    output_path = f"/openclaw/output/{spec['client']}_{spec['type']}.pptx"
    prs.save(output_path)
    return output_path
```

### Template Management

- Store master `.pptx` templates in `/openclaw/assets/templates/`
- Each template has a corresponding JSON schema defining required data fields
- Templates are versioned: `monthly_report_v2.pptx`, `monthly_report_v3.pptx`
- Active templates are referenced in a config file

## Limitations

| Limitation                  | Workaround                                      |
|-----------------------------|--------------------------------------------------|
| No animations               | Use static builds; animate in PowerPoint manually |
| No transitions              | Add transitions manually after generation        |
| Limited theme editing        | Design themes in PowerPoint, use as templates    |
| No video embedding          | Add video placeholder with instructions          |
| No SmartArt creation        | Build equivalent shapes manually or use images   |
| Large file sizes with images | Compress images with Pillow before embedding    |
| No presenter view config     | Must be configured manually                     |

## Performance Considerations

- Presentation generation typically takes 1-5 seconds for a 15-slide deck
- Image-heavy presentations: pre-compress images to reduce file size
- Chart rendering: native python-pptx charts render in PowerPoint; for custom charts, render with matplotlib and embed as images
- Memory: large presentations with many images can consume significant RAM; process and save incrementally if needed

## References

- python-pptx documentation: https://python-pptx.readthedocs.io/
- PyPI: https://pypi.org/project/python-pptx/
- GitHub: https://github.com/scanny/python-pptx

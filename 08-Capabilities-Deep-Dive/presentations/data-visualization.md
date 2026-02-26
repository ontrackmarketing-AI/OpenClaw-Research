# Data Visualization in AI-Generated Presentations

## Overview

Data visualization transforms raw metrics into compelling visual stories. For a marketing agency, the ability to automatically generate professional charts from CRM data, analytics platforms, and enrichment sources is critical for client reporting, strategy proposals, and pitch decks. This document covers the full stack: Python chart libraries, chart type selection by use case, data source integration, and embedding methods for both python-pptx and Google Slides.

## Python Chart Libraries

### matplotlib (Foundation Layer)

The most widely used Python charting library. Highly customizable but requires more code for polished output.

```bash
pip install matplotlib
```

```python
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from io import BytesIO

def create_leads_trend_chart(weeks, leads, conversions, brand_colors):
    """Generate a line chart showing weekly lead and conversion trends."""
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.plot(weeks, leads, color=brand_colors["primary"], linewidth=2.5,
            marker='o', markersize=6, label="Leads")
    ax.plot(weeks, conversions, color=brand_colors["accent"], linewidth=2.5,
            marker='s', markersize=6, label="Conversions")

    ax.set_title("Weekly Lead & Conversion Trends", fontsize=16, fontweight='bold',
                 color=brand_colors["text_dark"], pad=15)
    ax.set_xlabel("Week", fontsize=12)
    ax.set_ylabel("Count", fontsize=12)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()

    # Save to bytes buffer for embedding
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=200, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf
```

### plotly (Interactive and Publication Quality)

Produces beautiful charts with less code. Supports export to static images.

```bash
pip install plotly kaleido  # kaleido for static image export
```

```python
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO

def create_channel_breakdown(channels, values, brand_colors):
    """Pie chart showing lead distribution by marketing channel."""
    colors = [brand_colors["primary"], brand_colors["accent"],
              brand_colors["secondary"], "#6C757D", "#ADB5BD"]

    fig = go.Figure(data=[go.Pie(
        labels=channels,
        values=values,
        marker=dict(colors=colors[:len(channels)]),
        textinfo='label+percent',
        textfont_size=14,
        hole=0.35  # donut chart
    )])

    fig.update_layout(
        title=dict(text="Leads by Channel", font=dict(size=20)),
        font=dict(family="Open Sans"),
        showlegend=True,
        width=800, height=500,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    # Export to bytes
    img_bytes = fig.to_image(format="png", scale=2)
    return BytesIO(img_bytes)
```

### seaborn (Statistical Visualization)

Built on matplotlib, provides beautiful statistical charts with minimal code.

```bash
pip install seaborn
```

```python
import seaborn as sns
import matplotlib.pyplot as plt
from io import BytesIO

def create_comparison_heatmap(data_matrix, row_labels, col_labels):
    """Heatmap for competitor comparison or performance matrix."""
    fig, ax = plt.subplots(figsize=(10, 6))

    sns.heatmap(data_matrix, annot=True, fmt='.0f', cmap='YlOrRd',
                xticklabels=col_labels, yticklabels=row_labels,
                linewidths=0.5, ax=ax)

    ax.set_title("Competitor Performance Comparison", fontsize=16, fontweight='bold', pad=15)
    plt.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=200, bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf
```

## Chart Types by Use Case

### Performance Metrics

**Line Charts** -- Best for showing trends over time.

```python
# Use for: weekly leads, monthly revenue, traffic trends
# Data: time series from GHL API or Google Analytics
def performance_line_chart(dates, metrics_dict):
    fig, ax = plt.subplots(figsize=(10, 5))
    for label, values in metrics_dict.items():
        ax.plot(dates, values, linewidth=2, marker='o', label=label)
    ax.legend()
    ax.set_title("Performance Over Time")
    # ... styling ...
```

**Bar Charts** -- Best for comparisons between categories.

```python
# Use for: leads by source, revenue by service, performance by channel
def comparison_bar_chart(categories, values, title):
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(categories, values, color=brand_colors)
    # Add value labels on top of bars
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                str(val), ha='center', va='bottom', fontweight='bold')
    ax.set_title(title)
    # ... styling ...
```

### Budget and Spend

**Pie/Donut Charts** -- Budget allocation across channels.

```python
# Use for: ad spend distribution, budget allocation, revenue by service
# Keep to 5-7 segments maximum for readability
```

**Stacked Bar Charts** -- Budget breakdown over time.

```python
# Use for: monthly spend by channel, cost composition over quarters
def stacked_budget_chart(months, channel_data):
    fig, ax = plt.subplots(figsize=(10, 5))
    bottom = [0] * len(months)
    for channel, values in channel_data.items():
        ax.bar(months, values, bottom=bottom, label=channel)
        bottom = [b + v for b, v in zip(bottom, values)]
    ax.legend()
    ax.set_title("Monthly Budget Allocation")
```

**Waterfall Charts** -- Show how individual factors contribute to a total.

```python
# Use for: revenue breakdown, cost buildup, conversion drop-off
import plotly.graph_objects as go

def waterfall_chart(labels, values):
    fig = go.Figure(go.Waterfall(
        x=labels,
        y=values,
        measure=["relative"] * (len(values) - 1) + ["total"],
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": "#28A745"}},
        decreasing={"marker": {"color": "#DC3545"}},
        totals={"marker": {"color": "#007BFF"}}
    ))
    fig.update_layout(title="Revenue Waterfall", showlegend=False)
    return fig
```

### Conversion Funnel

```python
import plotly.graph_objects as go

def conversion_funnel(stages, counts):
    """
    Funnel chart for lead pipeline visualization.
    stages: ["Website Visitors", "Leads", "Qualified", "Meeting", "Proposal", "Closed"]
    counts: [5000, 450, 180, 75, 30, 12]
    """
    fig = go.Figure(go.Funnel(
        y=stages,
        x=counts,
        textinfo="value+percent initial",
        marker=dict(color=["#1A1A2E", "#2D2D5E", "#007BFF", "#28A745", "#FFC107", "#FF6B35"]),
        connector={"line": {"color": "royalblue", "dash": "dot", "width": 3}}
    ))

    fig.update_layout(
        title=dict(text="Lead Conversion Funnel", font=dict(size=20)),
        font=dict(family="Open Sans", size=14),
        width=800, height=500
    )

    img_bytes = fig.to_image(format="png", scale=2)
    return BytesIO(img_bytes)
```

### Geographic / Service Area

```python
import plotly.express as px

def service_area_heatmap(locations_data):
    """
    Heatmap showing lead density across service areas.
    locations_data: DataFrame with lat, lon, lead_count columns
    """
    fig = px.density_mapbox(
        locations_data,
        lat='lat', lon='lon', z='lead_count',
        radius=20,
        center=dict(lat=locations_data['lat'].mean(), lon=locations_data['lon'].mean()),
        zoom=10,
        mapbox_style="open-street-map",
        title="Lead Density by Location"
    )

    img_bytes = fig.to_image(format="png", scale=2, width=900, height=600)
    return BytesIO(img_bytes)
```

### Competitive Analysis

**Radar/Spider Charts** -- Multi-dimensional competitor comparison.

```python
import plotly.graph_objects as go

def competitor_radar(categories, client_scores, competitor_scores, competitor_name):
    """
    categories: ["SEO", "PPC", "Social", "Reviews", "Website", "Content"]
    scores: normalized 0-100 for each category
    """
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=client_scores + [client_scores[0]],  # close the polygon
        theta=categories + [categories[0]],
        fill='toself', name='Your Business',
        line_color='#007BFF', fillcolor='rgba(0,123,255,0.2)'
    ))

    fig.add_trace(go.Scatterpolar(
        r=competitor_scores + [competitor_scores[0]],
        theta=categories + [categories[0]],
        fill='toself', name=competitor_name,
        line_color='#DC3545', fillcolor='rgba(220,53,69,0.2)'
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        title=f"Competitive Comparison: You vs {competitor_name}",
        showlegend=True
    )

    img_bytes = fig.to_image(format="png", scale=2)
    return BytesIO(img_bytes)
```

## Data Sources

| Source | Data Available | Chart Types |
|--------|---------------|-------------|
| GHL API (Contacts) | Lead counts, sources, dates, tags | Line (trends), Bar (by source), Funnel |
| GHL API (Pipeline) | Opportunity stages, values, velocity | Funnel, Bar (by stage), Line (revenue) |
| Google Analytics | Traffic, sessions, bounce rate, conversions | Line (trends), Bar (channels), Pie (devices) |
| DataForSEO | Rankings, search volume, competitors | Line (rank changes), Bar (keyword gaps), Radar |
| Google Ads | Clicks, impressions, CTR, CPC, conversions | Line (trends), Bar (campaigns), Waterfall (spend) |
| Airtable | Custom metrics, project status, scores | Any (depends on data structure) |
| Google Places | Reviews, ratings, competitor locations | Bar (review comparison), Map (locations) |

## Embedding Charts in Presentations

### Method 1: python-pptx Native Charts

Use python-pptx's built-in chart support for simple charts that render natively in PowerPoint.

```python
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE
from pptx.util import Inches

chart_data = CategoryChartData()
chart_data.categories = ["Google Ads", "SEO", "Facebook", "Referral"]
chart_data.add_series("January", (45, 32, 18, 12))
chart_data.add_series("February", (52, 38, 22, 15))

chart_frame = slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED,
    Inches(1), Inches(1.5), Inches(10), Inches(5),
    chart_data
)

# Style the chart
chart = chart_frame.chart
chart.has_legend = True
chart.legend.include_in_layout = False
plot = chart.plots[0]
plot.gap_width = 120
```

**Pros:** Native rendering, editable in PowerPoint, small file size.
**Cons:** Limited chart types, less visual customization.

### Method 2: Embed as Image (Recommended for Complex Charts)

Generate charts with matplotlib/plotly, export as PNG, embed in slide.

```python
from pptx.util import Inches
from io import BytesIO

# Generate chart image
chart_buffer = create_leads_trend_chart(weeks, leads, conversions, brand_colors)

# Embed in slide
slide.shapes.add_picture(
    chart_buffer,
    Inches(1), Inches(1.5),     # position
    Inches(10), Inches(5)       # size
)
```

**Pros:** Full control over appearance, any chart type, consistent rendering.
**Cons:** Not editable in PowerPoint, larger file size, raster image.

### Method 3: Google Slides (Image Upload)

For Google Slides, upload chart images to Google Drive or a public URL, then reference.

```python
# 1. Generate chart
chart_buffer = create_funnel_chart(stages, counts)

# 2. Upload to Google Drive
file_metadata = {'name': 'funnel_chart.png', 'mimeType': 'image/png'}
media = MediaIoBaseUpload(chart_buffer, mimetype='image/png')
uploaded = drive_service.files().create(
    body=file_metadata, media_body=media, fields='id,webContentLink'
).execute()

# 3. Make publicly accessible
drive_service.permissions().create(
    fileId=uploaded['id'],
    body={'type': 'anyone', 'role': 'reader'}
).execute()

# 4. Embed in Google Slides
requests = [{
    'createImage': {
        'url': uploaded['webContentLink'],
        'elementProperties': {
            'pageObjectId': slide_id,
            'size': {'width': {'magnitude': 500, 'unit': 'PT'},
                     'height': {'magnitude': 300, 'unit': 'PT'}},
            'transform': {'scaleX': 1, 'scaleY': 1,
                         'translateX': 50, 'translateY': 100, 'unit': 'PT'}
        }
    }
}]
```

## Real-Time Data Chart Generation

### Flow for Live Data Charts

```
Request to generate report
    -> Query GHL API for latest contact/pipeline data
    -> Query Google Analytics for traffic data
    -> Query DataForSEO for SEO data
    -> Aggregate and calculate metrics
    -> Generate chart images from live data
    -> Embed charts into presentation template
    -> Save/share presentation
```

### Caching Strategy

```python
import hashlib
import json
from datetime import datetime, timedelta

CHART_CACHE = {}
CACHE_TTL = timedelta(hours=1)

def get_or_generate_chart(chart_type, data, brand_colors):
    """Cache chart images to avoid regeneration for same data."""
    cache_key = hashlib.md5(
        json.dumps({"type": chart_type, "data": data}, sort_keys=True).encode()
    ).hexdigest()

    if cache_key in CHART_CACHE:
        cached = CHART_CACHE[cache_key]
        if datetime.now() - cached["timestamp"] < CACHE_TTL:
            return cached["image"]

    # Generate chart
    chart_generators = {
        "leads_trend": create_leads_trend_chart,
        "channel_breakdown": create_channel_breakdown,
        "conversion_funnel": conversion_funnel,
        "competitor_radar": competitor_radar,
    }

    image_buffer = chart_generators[chart_type](data, brand_colors)

    CHART_CACHE[cache_key] = {
        "image": image_buffer,
        "timestamp": datetime.now()
    }

    return image_buffer
```

## Styling Best Practices

### Brand Color Consistency

```python
# Define a chart color palette derived from brand colors
def get_chart_palette(brand_config):
    """Generate a full chart palette from brand primary/accent colors."""
    return {
        "series_colors": [
            brand_config["primary"],
            brand_config["accent"],
            lighten(brand_config["primary"], 0.3),
            lighten(brand_config["accent"], 0.3),
            "#6C757D",  # neutral gray for additional series
        ],
        "background": "#FFFFFF",
        "grid_color": "#E9ECEF",
        "text_color": brand_config.get("text_dark", "#1A1A2E"),
        "positive": "#28A745",
        "negative": "#DC3545",
        "neutral": "#6C757D"
    }
```

### Design Rules

1. **One key insight per chart.** Do not overload a single chart with too many data series.
2. **Clear titles.** Every chart must have a title that states the insight, not just the metric name. Example: "Leads Increased 35% in January" instead of "Monthly Leads."
3. **Data source citation.** Include a small footnote: "Source: GoHighLevel CRM, Jan 1-31, 2026."
4. **Consistent axes.** Use the same scale when comparing charts across slides.
5. **Limit colors.** Use 2-5 colors per chart. More than 5 segments becomes hard to read.
6. **Labels over legends.** Direct labels on chart elements are more readable than separate legends.
7. **Remove clutter.** Hide gridlines where unnecessary, remove chart borders, use clean backgrounds.
8. **Accessible colors.** Ensure color choices work for color-blind viewers (avoid red/green only distinctions).

## Interactive Presentations (Web-Based)

For cases where a web-based presentation is appropriate:

### Reveal.js with Plotly

```html
<!-- Embed interactive plotly charts in Reveal.js slides -->
<section>
    <h2>Lead Conversion Funnel</h2>
    <div id="funnel-chart" style="width:800px;height:500px;"></div>
    <script>
        Plotly.newPlot('funnel-chart', funnelData, funnelLayout);
    </script>
</section>
```

### Marp (Markdown to Slides)

```markdown
---
marp: true
theme: agency
---

# Monthly Performance

![Lead Trend Chart](./charts/leads_trend.png)

*Source: GoHighLevel CRM*
```

These are alternatives to PowerPoint/Google Slides for specific use cases like internal reviews or tech-savvy clients.

## Chart Generation Pipeline for OpenClaw

```python
async def generate_all_report_charts(client_id: str, period: str) -> dict:
    """
    Generate all charts needed for a monthly report.
    Returns dict of chart_name -> BytesIO image buffer.
    """
    # 1. Fetch all data in parallel
    data = await fetch_report_data(client_id, period)
    brand = await get_client_brand(client_id)
    palette = get_chart_palette(brand)

    charts = {}

    # 2. Generate each chart
    charts["leads_trend"] = create_leads_trend_chart(
        data["weekly_dates"], data["weekly_leads"], data["weekly_conversions"], palette
    )

    charts["channel_breakdown"] = create_channel_breakdown(
        data["channel_names"], data["channel_lead_counts"], palette
    )

    charts["conversion_funnel"] = conversion_funnel(
        data["pipeline_stages"], data["pipeline_counts"]
    )

    charts["budget_allocation"] = create_budget_pie(
        data["channels"], data["spend_by_channel"], palette
    )

    if data.get("competitor_data"):
        charts["competitor_radar"] = competitor_radar(
            data["comparison_categories"],
            data["client_scores"],
            data["competitor_scores"],
            data["top_competitor_name"]
        )

    return charts
```

## References

- matplotlib documentation: https://matplotlib.org/stable/
- plotly Python documentation: https://plotly.com/python/
- seaborn documentation: https://seaborn.pydata.org/
- python-pptx chart documentation: https://python-pptx.readthedocs.io/en/latest/user/charts.html

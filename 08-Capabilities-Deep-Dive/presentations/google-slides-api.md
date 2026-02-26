# Google Slides API: Cloud-Based Presentation Creation

## Overview

The Google Slides API enables programmatic creation and editing of Google Slides presentations. Unlike python-pptx which generates local files, the Slides API creates cloud-native presentations that are instantly shareable, collaborative, and accessible from any browser. For OpenClaw, this provides a way to generate presentations that clients can immediately view, comment on, and edit within Google Workspace.

## Setup Requirements

### 1. Google Cloud Project

```
1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing): "OpenClaw Presentations"
3. Enable the Google Slides API
4. Enable the Google Drive API (needed for file sharing/management)
5. Enable the Google Sheets API (optional, for chart data)
```

### 2. Service Account Authentication (Recommended for Automation)

```
1. In Google Cloud Console -> IAM & Admin -> Service Accounts
2. Create service account: "openclaw-slides@project-id.iam.gserviceaccount.com"
3. Create JSON key file -> download and store securely
4. No domain-wide delegation needed for basic use
```

### 3. Environment Setup

```bash
pip install google-api-python-client google-auth google-auth-httplib2 google-auth-oauthlib
```

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/drive'
]

credentials = service_account.Credentials.from_service_account_file(
    '/path/to/service-account-key.json',
    scopes=SCOPES
)

slides_service = build('slides', 'v1', credentials=credentials)
drive_service = build('drive', 'v3', credentials=credentials)
```

## Core Operations

### Creating a Blank Presentation

```python
presentation = slides_service.presentations().create(
    body={'title': 'Monthly Report - ABC Plumbing'}
).execute()

presentation_id = presentation['presentationId']
print(f"Created: https://docs.google.com/presentation/d/{presentation_id}")
```

### Adding a Slide

```python
requests = [
    {
        'createSlide': {
            'objectId': 'slide_001',
            'insertionIndex': 0,
            'slideLayoutReference': {
                'predefinedLayout': 'TITLE'  # TITLE, TITLE_AND_BODY, BLANK, etc.
            }
        }
    }
]

slides_service.presentations().batchUpdate(
    presentationId=presentation_id,
    body={'requests': requests}
).execute()
```

### Adding Text to a Slide

```python
requests = [
    # Insert text into the title placeholder
    {
        'insertText': {
            'objectId': 'slide_001_title',  # placeholder object ID
            'text': 'January 2026 Performance Report',
            'insertionIndex': 0
        }
    },
    # Style the text
    {
        'updateTextStyle': {
            'objectId': 'slide_001_title',
            'style': {
                'fontSize': {'magnitude': 32, 'unit': 'PT'},
                'foregroundColor': {
                    'opaqueColor': {
                        'rgbColor': {'red': 0.1, 'green': 0.1, 'blue': 0.18}
                    }
                },
                'fontFamily': 'Montserrat',
                'bold': True
            },
            'textRange': {'type': 'ALL'},
            'fields': 'fontSize,foregroundColor,fontFamily,bold'
        }
    }
]

slides_service.presentations().batchUpdate(
    presentationId=presentation_id,
    body={'requests': requests}
).execute()
```

### Adding an Image

```python
requests = [
    {
        'createImage': {
            'objectId': 'logo_image',
            'url': 'https://example.com/client-logo.png',  # Must be publicly accessible URL
            'elementProperties': {
                'pageObjectId': 'slide_001',
                'size': {
                    'width': {'magnitude': 200, 'unit': 'PT'},
                    'height': {'magnitude': 100, 'unit': 'PT'}
                },
                'transform': {
                    'scaleX': 1, 'scaleY': 1,
                    'translateX': 50, 'translateY': 30,
                    'unit': 'PT'
                }
            }
        }
    }
]
```

### Creating a Table

```python
requests = [
    {
        'createTable': {
            'objectId': 'metrics_table',
            'elementProperties': {
                'pageObjectId': 'slide_002',
                'size': {
                    'width': {'magnitude': 600, 'unit': 'PT'},
                    'height': {'magnitude': 300, 'unit': 'PT'}
                },
                'transform': {
                    'scaleX': 1, 'scaleY': 1,
                    'translateX': 50, 'translateY': 120,
                    'unit': 'PT'
                }
            },
            'rows': 5,
            'columns': 3
        }
    },
    # Insert text into table cells
    {
        'insertText': {
            'objectId': 'metrics_table',
            'cellLocation': {'rowIndex': 0, 'columnIndex': 0},
            'text': 'Metric',
            'insertionIndex': 0
        }
    }
]
```

## Template-Based Approach (Recommended)

The most efficient approach is to design a polished template in Google Slides, then copy and populate it programmatically.

### Copy Template and Replace Placeholders

```python
def create_from_template(template_id, title, replacements):
    """
    template_id: Google Slides ID of the master template
    title: name for the new presentation
    replacements: dict of {{placeholder}} -> value mappings
    """
    # Step 1: Copy the template
    copied = drive_service.files().copy(
        fileId=template_id,
        body={'name': title}
    ).execute()
    new_id = copied['id']

    # Step 2: Build replacement requests
    requests = []
    for placeholder, value in replacements.items():
        requests.append({
            'replaceAllText': {
                'containsText': {
                    'text': '{{' + placeholder + '}}',
                    'matchCase': True
                },
                'replaceText': str(value)
            }
        })

    # Step 3: Execute replacements
    if requests:
        slides_service.presentations().batchUpdate(
            presentationId=new_id,
            body={'requests': requests}
        ).execute()

    return new_id

# Usage
new_presentation_id = create_from_template(
    template_id='1ABC123_template_id_here',
    title='ABC Plumbing - January Report',
    replacements={
        'client_name': 'ABC Plumbing',
        'report_month': 'January 2026',
        'total_leads': '147',
        'conversion_rate': '12.4%',
        'revenue': '$24,500',
        'top_source': 'Google Ads',
        'recommendation_1': 'Increase Google Ads budget by 20%',
        'recommendation_2': 'Launch Facebook retargeting campaign',
        'recommendation_3': 'Optimize landing page for mobile'
    }
)
```

### Replacing Images in Templates

```python
# Replace a placeholder image with a chart or logo
requests = [
    {
        'replaceAllShapesWithImage': {
            'imageUrl': 'https://your-server.com/charts/leads_chart.png',
            'imageReplaceMethod': 'CENTER_INSIDE',
            'containsText': {
                'text': '{{chart_leads}}',
                'matchCase': True
            }
        }
    }
]
```

## Sharing Presentations

```python
def share_with_client(presentation_id, client_email, role='reader'):
    """Share presentation with client. Roles: reader, writer, commenter"""
    drive_service.permissions().create(
        fileId=presentation_id,
        body={
            'type': 'user',
            'role': role,
            'emailAddress': client_email
        },
        sendNotificationEmail=True,
        emailMessage='Your monthly report is ready! Click the link to view.'
    ).execute()

    # Get shareable link
    link = f"https://docs.google.com/presentation/d/{presentation_id}/edit?usp=sharing"
    return link

# Share as viewer
link = share_with_client(new_presentation_id, 'client@abcplumbing.com', 'reader')

# Anyone with link can view
drive_service.permissions().create(
    fileId=new_presentation_id,
    body={
        'type': 'anyone',
        'role': 'reader'
    }
).execute()
```

## Speaker Notes

```python
requests = [
    {
        'insertText': {
            'objectId': 'slide_001_notes',  # notes page object ID
            'text': 'Key talking points:\n- Revenue up 15% MoM\n- Google Ads driving 60% of leads\n- Recommend increasing budget',
            'insertionIndex': 0
        }
    }
]
```

## Predefined Slide Layouts

| Layout Name            | Description                              | Use Case                    |
|------------------------|------------------------------------------|-----------------------------|
| BLANK                  | Empty slide                              | Custom content              |
| CAPTION_ONLY           | Caption at bottom                        | Image slides                |
| MAIN_POINT             | Large centered text                      | Key takeaways               |
| BIG_NUMBER             | Large number display                     | KPI highlights              |
| SECTION_HEADER         | Section divider                          | Between report sections     |
| SECTION_TITLE_AND_DESCRIPTION | Title with description          | Section intros              |
| TITLE                  | Title slide                              | Cover page                  |
| TITLE_AND_BODY         | Title with content area                  | Standard content            |
| TITLE_AND_TWO_COLUMNS  | Title with two columns                   | Comparisons                 |
| ONE_COLUMN_TEXT        | Single column of text                    | Detailed content            |

## Integration with OpenClaw

### As a Presentation Skill

```python
async def create_google_slides_report(spec: dict) -> str:
    """
    Creates a Google Slides presentation from template and returns shareable link.

    spec = {
        "template_id": "1ABC...",          # Google Slides template ID
        "title": "Client Monthly Report",
        "replacements": {                   # text replacements
            "client_name": "ABC Plumbing",
            ...
        },
        "charts": [                         # charts to generate and embed
            {"type": "line", "data": {...}, "placeholder": "chart_leads"}
        ],
        "share_with": ["client@example.com"],
        "share_role": "reader"
    }
    """
    # 1. Copy template
    new_id = copy_template(spec["template_id"], spec["title"])

    # 2. Replace text placeholders
    replace_text(new_id, spec["replacements"])

    # 3. Generate and embed charts
    for chart in spec.get("charts", []):
        chart_url = generate_chart_image(chart)  # render chart, upload, get URL
        replace_image(new_id, chart["placeholder"], chart_url)

    # 4. Share with client
    for email in spec.get("share_with", []):
        share_with_client(new_id, email, spec.get("share_role", "reader"))

    return f"https://docs.google.com/presentation/d/{new_id}/edit?usp=sharing"
```

## API Quotas and Rate Limits

| Quota                        | Limit                          |
|------------------------------|--------------------------------|
| Read requests per minute     | 300 per minute per project     |
| Write requests per minute    | 60 per minute per project      |
| Presentations per day        | No explicit limit, but rate-limited |
| File size                    | 100 MB max                     |
| Slides per presentation      | 1,000 max (practical ~200)     |

Best practice: batch multiple operations into a single `batchUpdate` call to minimize API calls.

## Cost

- Google Slides API is free to use (no per-call charges)
- Requires a Google Workspace account or personal Google account
- For service account access, a Google Workspace domain is recommended
- Storage counts against Google Drive quota (15 GB free, or Workspace plan)

## Comparison with python-pptx

| Feature             | Google Slides API              | python-pptx                    |
|---------------------|--------------------------------|--------------------------------|
| Output format       | Google Slides (cloud)          | .pptx (local file)            |
| Collaboration       | Real-time, built-in            | None (file-based)              |
| Sharing             | Instant link sharing           | Requires file transfer         |
| Offline access      | Limited                        | Full offline support           |
| Design control      | Medium (API limitations)       | High (full XML access)         |
| Charts              | Limited (use images)           | Native chart support           |
| Animations          | Limited API support            | Not supported                  |
| Dependency          | Internet + Google account      | None (pure Python)             |
| Speed               | Slower (network calls)         | Faster (local processing)      |
| Export to PDF       | Via Drive API                  | Requires LibreOffice/PowerPoint |

## Recommendation for OpenClaw

Use **both** approaches:
- **Google Slides API** for presentations that need to be shared with clients immediately, commented on collaboratively, or embedded in emails as links
- **python-pptx** for presentations that need to be downloaded, attached to emails, or require complex chart layouts not easily done via the Slides API
- Generate charts with matplotlib/plotly, upload to cloud storage, and reference URLs in Google Slides
- Maintain templates in both formats: `.pptx` files and Google Slides template documents

## References

- Google Slides API documentation: https://developers.google.com/slides
- Google Slides API Python quickstart: https://developers.google.com/slides/api/quickstart/python
- API reference: https://developers.google.com/slides/api/reference/rest

# OCR Engine Selection: Tesseract vs AWS Textract vs Google Document AI vs Azure Document Intelligence

## Overview

Steven's business handles scanned contracts, invoices, legal documents, and handwritten notes
that need to be digitized and fed into the knowledge base. This document compares four OCR
engines to determine the best fit for OpenClaw's document processing pipeline, considering
accuracy, cost, deployment model, and integration complexity.

**Decision Criteria:**
1. **Accuracy** on printed text, tables, forms, and handwriting
2. **Table extraction** quality (contracts with structured data)
3. **Cost** at projected volume (~100-500 pages/month)
4. **Deployment** compatibility (Mac Mini self-hosted vs cloud API)
5. **Integration** complexity with n8n/Supabase pipeline
6. **Language support** (primarily English, some Spanish)

---

## API/Integration Details

### Engine Comparison Matrix

| Feature | Tesseract | AWS Textract | Google Document AI | Azure Document Intelligence |
|---------|-----------|-------------|-------------------|---------------------------|
| **Type** | Open-source library | Cloud API | Cloud API | Cloud API |
| **Deployment** | Self-hosted (Mac Mini) | AWS Cloud | Google Cloud | Azure Cloud |
| **Printed Text Accuracy** | 95-98% (clean scans) | 95-99% | 97-99% | 97-99% |
| **Handwriting Accuracy** | Poor (50-70%) | Good (85-90%) | Very Good (90%+, 50 langs) | Very Good (90%+) |
| **Table Extraction** | None (manual post-processing) | Native (excellent) | Native (Form Parser) | Native (excellent) |
| **Form Key-Value Pairs** | None | Native | Native (Form Parser) | Native |
| **Languages** | 100+ via language packs | Limited (no CJK) | Broadest (global) | Broad (global) |
| **Confidence Scores** | Per-word confidence | Per-word/block confidence | Per-entity confidence | Per-field confidence |
| **PDF Support** | Via pdf2image conversion | Native PDF input | Native PDF input | Native PDF input |
| **Batch Processing** | Local parallel processing | Async (StartDocumentAnalysis) | Batch API | Async operations |
| **Offline Capable** | Yes (fully offline) | No | No | No |
| **Free Tier** | Unlimited (open source) | 1,000 pages/mo (3 months) | None | None |
| **Latency** | 1-5s/page (local) | 2-10s/page (API) | 2-8s/page (API) | 2-8s/page (API) |

### Detailed Engine Profiles

#### 1. Tesseract OCR (Open Source)

**Version:** Tesseract 5.x with LSTM engine
**Python Wrapper:** pytesseract

**Strengths:**
- Completely free and self-hosted on Mac Mini
- No API calls, no rate limits, no per-page costs
- Excellent on clean, well-scanned printed text
- 100+ language packs available
- Creates searchable PDFs natively
- Full control over preprocessing pipeline

**Weaknesses:**
- Poor handwriting recognition
- No native table extraction (must build custom logic)
- No form key-value pair detection
- Struggles with noisy scans, skewed images, multi-column layouts
- Requires extensive image preprocessing for good results

**Basic Usage:**
```python
import pytesseract
from PIL import Image

# Simple text extraction
text = pytesseract.image_to_string(Image.open('document.png'))

# With confidence data
data = pytesseract.image_to_data(Image.open('document.png'), output_type=pytesseract.Output.DICT)
for i, conf in enumerate(data['conf']):
    if int(conf) > 60:  # Filter low-confidence words
        print(f"{data['text'][i]} (confidence: {conf}%)")

# PDF to searchable PDF
pdf_bytes = pytesseract.image_to_pdf_or_hocr(Image.open('scan.png'), extension='pdf')
```

**Preprocessing Required:**
```python
import cv2
import numpy as np

def preprocess_for_tesseract(image_path: str) -> np.ndarray:
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)        # Grayscale
    denoised = cv2.medianBlur(gray, 3)                    # Denoise
    thresh = cv2.adaptiveThreshold(                       # Binarize
        denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )
    # Deskew if needed
    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = thresh.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(thresh, M, (w, h),
                              flags=cv2.INTER_CUBIC,
                              borderMode=cv2.BORDER_REPLICATE)
    return rotated
```

#### 2. AWS Textract

**Endpoints:**
| Operation | Endpoint | Per-Page Cost (1st 1M) |
|-----------|----------|----------------------|
| DetectDocumentText | Sync/Async | $0.0015 |
| AnalyzeDocument (Tables) | Sync/Async | $0.015 |
| AnalyzeDocument (Forms) | Sync/Async | $0.05 |
| AnalyzeDocument (Tables+Forms) | Sync/Async | $0.065 |
| AnalyzeDocument (Queries) | Sync/Async | $0.015 |
| AnalyzeExpense | Sync/Async | $0.01 |
| AnalyzeID | Sync | $0.025 |

**Strengths:**
- Excellent table and form extraction out of the box
- Queries feature: ask natural language questions about documents
- Native AWS ecosystem integration (S3, Lambda, Step Functions)
- Good accuracy on printed text and forms
- Async processing for large documents

**Weaknesses:**
- No CJK language support (Chinese, Japanese, Korean)
- Per-page costs add up with Tables+Forms feature
- Requires AWS account and IAM setup
- No offline capability

**Usage Example:**
```python
import boto3

textract = boto3.client('textract', region_name='us-west-2')

# Analyze document for tables and forms
response = textract.analyze_document(
    Document={'Bytes': open('document.pdf', 'rb').read()},
    FeatureTypes=['TABLES', 'FORMS']
)

# Extract tables
for block in response['Blocks']:
    if block['BlockType'] == 'TABLE':
        # Process table structure
        pass
    elif block['BlockType'] == 'KEY_VALUE_SET':
        # Process form key-value pairs
        pass
```

#### 3. Google Document AI

**Processor Types:**
| Processor | Cost per 1,000 pages | Best For |
|-----------|---------------------|----------|
| Enterprise Document OCR | $1.50 | Basic text extraction |
| Form Parser | $30.00 | Forms + tables + key-value |
| Layout Parser | $10.00 | Complex document layouts |
| Invoice Parser | $10/100 pages | Invoice processing |
| Custom Extractor | $30.00 | Domain-specific extraction |

**Strengths:**
- Broadest language support (including handwriting in 50 languages)
- Excellent layout understanding (multi-column, mixed content)
- Math/formula recognition
- Font style detection
- Pre-trained specialized processors (invoices, receipts, IDs)

**Weaknesses:**
- No free tier
- Form Parser is expensive ($30/1,000 pages)
- Requires Google Cloud project setup
- Complex processor provisioning workflow

**Usage Example:**
```python
from google.cloud import documentai_v1 as documentai

client = documentai.DocumentProcessorServiceClient()
processor_name = f"projects/{project_id}/locations/us/processors/{processor_id}"

with open('document.pdf', 'rb') as f:
    raw_document = documentai.RawDocument(
        content=f.read(),
        mime_type='application/pdf'
    )

request = documentai.ProcessRequest(
    name=processor_name,
    raw_document=raw_document
)

result = client.process_document(request=request)
document = result.document

# Extract text
print(document.text)

# Extract tables
for page in document.pages:
    for table in page.tables:
        for row in table.body_rows:
            for cell in row.cells:
                print(cell.layout.text_anchor.text_segments)
```

#### 4. Azure Document Intelligence (formerly Form Recognizer)

**Pricing:**
| Feature | Cost per 1,000 pages |
|---------|---------------------|
| Read (OCR) | $1.50 |
| Layout (tables + structure) | ~$10.00 |
| Prebuilt Models (invoice, receipt, ID) | ~$10.00 |
| Custom Models | ~$50.00 |
| Custom Neural Model Training | $3/hr (after 10 free hours) |

**Strengths:**
- Best-in-class on irregular/older invoices and forms
- Strong table extraction with cell-level confidence
- Pre-built models for common document types
- Custom neural models for domain-specific documents
- Integrates with Azure AI ecosystem

**Weaknesses:**
- Requires Azure account and resource provisioning
- Custom model training costs can add up
- API complexity (multiple model types to choose from)

**Usage Example:**
```python
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential

client = DocumentAnalysisClient(
    endpoint="https://<resource>.cognitiveservices.azure.com/",
    credential=AzureKeyCredential("<key>")
)

with open('document.pdf', 'rb') as f:
    poller = client.begin_analyze_document("prebuilt-layout", f)
    result = poller.result()

for table in result.tables:
    print(f"Table: {table.row_count} rows x {table.column_count} columns")
    for cell in table.cells:
        print(f"  [{cell.row_index},{cell.column_index}]: {cell.content}")
```

---

## Implementation Approach

### Recommended Strategy: Hybrid (Tesseract + AWS Textract)

Given Steven's volume (~100-500 pages/month) and infrastructure (Mac Mini):

| Document Type | Engine | Reason |
|---------------|--------|--------|
| Clean printed text (contracts, letters) | Tesseract (local) | Free, fast, sufficient accuracy |
| Tables and forms (invoices, applications) | AWS Textract | Native table extraction, low cost |
| Handwritten notes | AWS Textract | Tesseract cannot handle handwriting |
| High-volume batch (quarterly cleanup) | Tesseract (local) | No per-page cost |

### Decision Flow
```
Document arrives
    |
    v
[Classify document type]
    |
    +-- Clean printed text? --> Tesseract (local, free)
    |
    +-- Contains tables/forms? --> AWS Textract ($0.015-0.065/page)
    |
    +-- Handwritten content? --> AWS Textract ($0.0015/page)
    |
    +-- Complex layout? --> AWS Textract with Queries
```

### Why Not Google or Azure?

- **Google Document AI**: Form Parser at $30/1,000 pages is 20x more expensive than Textract Tables.
  Enterprise OCR at $1.50/1,000 is competitive, but Tesseract is free for the same job.
- **Azure Document Intelligence**: Similar pricing to Google. Good quality, but no clear advantage
  over Textract for our use case, and Steven already uses AWS infrastructure.

---

## Cost Implications

### Monthly Cost Projections (100-500 pages/month)

| Scenario | Tesseract Only | Textract Only | Hybrid (Recommended) |
|----------|---------------|--------------|---------------------|
| 100 pages/mo | $0 | $1.50-6.50 | $0.75-3.25 |
| 250 pages/mo | $0 | $3.75-16.25 | $1.88-8.13 |
| 500 pages/mo | $0 | $7.50-32.50 | $3.75-16.25 |

*Textract range: low = DetectText only, high = Tables+Forms on every page.*
*Hybrid assumes 50% Tesseract (clean text) + 50% Textract (tables/forms).*

### Annual Cost Comparison (at 250 pages/month)

| Engine | Annual Cost | Notes |
|--------|-------------|-------|
| Tesseract only | $0 | Miss tables/handwriting |
| Hybrid (recommended) | $23-98/year | Best balance of cost and capability |
| Textract only | $45-195/year | Overkill for clean text |
| Google Document AI | $90-360/year | Expensive, no clear advantage |
| Azure Document Intelligence | $45-300/year | Similar to Textract, no AWS synergy |

### Free Tier Considerations
- **Tesseract**: Always free (open source)
- **AWS Textract**: 1,000 pages/month free for 3 months (new account)
- **Google Document AI**: No free tier
- **Azure**: No free tier for Document Intelligence

---

## Estimated Build Hours

| Task | Hours |
|------|-------|
| Tesseract setup on Mac Mini (install + configure) | 2-3 |
| Image preprocessing pipeline (OpenCV) | 4-6 |
| AWS Textract integration (boto3 + IAM) | 3-4 |
| Document classifier (route to correct engine) | 3-4 |
| Table extraction post-processing | 4-6 |
| Confidence scoring + quality checks | 2-3 |
| Supabase storage integration | 2-3 |
| n8n workflow orchestration | 3-4 |
| Testing with sample documents | 4-6 |
| **Total** | **27-39 hours** |

### Hardware Requirements (Mac Mini)
- Tesseract 5.x: ~200MB disk, minimal RAM
- Python + OpenCV + pytesseract: ~500MB disk
- Processing speed: ~1-5 seconds per page (depends on preprocessing)
- No GPU required (Tesseract uses CPU-based LSTM)

### Dependencies
- [ ] Tesseract 5.x installed on Mac Mini (`brew install tesseract`)
- [ ] Python 3.10+ with pytesseract, opencv-python, pdf2image, Pillow
- [ ] AWS account with Textract access (for table/form/handwriting)
- [ ] Poppler (for pdf2image PDF-to-PNG conversion)
- [ ] n8n instance with Code node capability
- [ ] Supabase table for document storage and metadata

---

## Accuracy Benchmarks (Industry Reports, 2025)

| Test Scenario | Tesseract | Textract | Google Doc AI | Azure Doc Intel |
|--------------|-----------|----------|--------------|-----------------|
| Clean printed text | 97% | 98% | 99% | 98% |
| Noisy/degraded scans | 80% | 93% | 95% | 94% |
| Handwriting (English) | 55% | 88% | 92% | 91% |
| Table structure | N/A* | 94% | 93% | 95% |
| Form key-value pairs | N/A* | 93% | 91% | 94% |
| Multi-column layout | 75% | 90% | 95% | 92% |
| Invoice fields | N/A* | 95% | 96% | 97% |

*Tesseract has no native table/form extraction. Custom post-processing required.*

Source: Aggregated from [MarkTechPost 2025 OCR Comparison](https://www.marktechpost.com/2025/11/02/comparing-the-top-6-ocr-optical-character-recognition-models-systems-in-2025/), [Pragmile OCR Ranking 2025](https://pragmile.com/ocr-ranking-2025-comparison-of-the-best-text-recognition-and-document-structure-software/), [BusinessWareTech Benchmark](https://www.businesswaretech.com/blog/research-best-ai-services-for-automatic-invoice-processing).

---

## Recommendation

**Use the Hybrid approach (Tesseract + AWS Textract):**

1. **Tesseract** for clean printed documents (contracts, letters, standard correspondence) — free and fast
2. **AWS Textract** for anything with tables, forms, handwriting, or complex layouts — accurate and affordable
3. Start with Tesseract for everything, add Textract incrementally for documents where Tesseract falls short
4. Re-evaluate in 6 months: if volume exceeds 1,000 pages/month, consider Google Document AI's Enterprise OCR tier

---

## References

- [Tesseract OCR GitHub](https://github.com/tesseract-ocr/tesseract)
- [pytesseract Documentation](https://pypi.org/project/pytesseract/)
- [AWS Textract Pricing](https://aws.amazon.com/textract/pricing/)
- [AWS Textract Documentation](https://docs.aws.amazon.com/textract/)
- [Google Document AI Pricing](https://cloud.google.com/document-ai/pricing)
- [Azure Document Intelligence Pricing](https://azure.microsoft.com/en-us/pricing/details/document-intelligence/)
- [MarkTechPost OCR Comparison 2025](https://www.marktechpost.com/2025/11/02/comparing-the-top-6-ocr-optical-character-recognition-models-systems-in-2025/)
- [Pragmile OCR Ranking 2025](https://pragmile.com/ocr-ranking-2025-comparison-of-the-best-text-recognition-and-document-structure-software/)
- [IntuitionLabs AI OCR Comparison](https://intuitionlabs.ai/articles/ai-ocr-models-pdf-structured-text-comparison)

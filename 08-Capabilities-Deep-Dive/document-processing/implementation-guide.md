# OCR Pipeline Implementation Guide

## Overview

This guide covers the end-to-end implementation of the document processing pipeline for
OpenClaw. The pipeline takes scanned PDFs, images, and photos of documents, runs them through
OCR (Tesseract locally or AWS Textract for complex documents), extracts structured data
(text, tables, key-value pairs), scores confidence, and stores results in the Supabase
knowledge base for retrieval by the AI voice bot and CRM.

**Pipeline Architecture:**
```
Document Input (scan, photo, PDF upload)
    |
    v
[1. Intake & Classification]
    - Detect document type (contract, invoice, letter, handwritten)
    - Route to appropriate OCR engine
    |
    v
[2. Image Preprocessing]
    - PDF to image conversion (if needed)
    - Grayscale, deskew, denoise, binarize
    |
    v
[3. OCR Extraction]
    - Tesseract (clean printed text)
    - AWS Textract (tables, forms, handwriting)
    |
    v
[4. Post-Processing]
    - Confidence scoring & filtering
    - Table structure reconstruction
    - Entity extraction (names, dates, amounts)
    |
    v
[5. Storage & Indexing]
    - Raw text to Supabase
    - Vector embeddings for semantic search
    - Metadata tagging (type, date, confidence, source)
    |
    v
[6. Knowledge Base Integration]
    - AI voice bot can query processed documents
    - CRM notes linked to source documents
    - Full-text and semantic search available
```

---

## API/Integration Details

### Technology Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| PDF Conversion | pdf2image + Poppler | Convert PDF pages to PNG images |
| Image Processing | OpenCV (cv2) | Preprocessing (denoise, deskew, threshold) |
| Local OCR | Tesseract 5.x + pytesseract | Free OCR for clean printed text |
| Cloud OCR | AWS Textract (boto3) | Table/form/handwriting extraction |
| Text Processing | spaCy / regex | Entity extraction (names, dates, amounts) |
| Vector Embeddings | OpenAI text-embedding-3-small | Semantic search indexing |
| Storage | Supabase (PostgreSQL + pgvector) | Document text, metadata, embeddings |
| Orchestration | n8n | Workflow automation and routing |
| File Storage | Supabase Storage / S3 | Original document archive |

### Supabase Schema

```sql
-- Document metadata table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,           -- Supabase Storage path
    document_type TEXT,                 -- contract, invoice, letter, handwritten, unknown
    page_count INTEGER,
    ocr_engine TEXT,                    -- tesseract, textract, manual
    overall_confidence FLOAT,           -- 0.0 - 1.0 average confidence
    status TEXT DEFAULT 'pending',      -- pending, processing, completed, failed
    source TEXT,                        -- upload, email, scan
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    nutshell_contact_id INTEGER,        -- Link to CRM contact
    nutshell_lead_id INTEGER,           -- Link to CRM lead
    metadata JSONB DEFAULT '{}'         -- Flexible additional fields
);

-- Extracted text pages
CREATE TABLE document_pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    raw_text TEXT,                       -- Full extracted text
    confidence FLOAT,                   -- Page-level confidence score
    word_count INTEGER,
    low_confidence_words INTEGER,       -- Count of words below threshold
    ocr_engine TEXT,                    -- Engine used for this page
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Extracted tables
CREATE TABLE document_tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    table_index INTEGER DEFAULT 0,      -- Multiple tables per page
    row_count INTEGER,
    column_count INTEGER,
    headers JSONB,                      -- ["Column A", "Column B", ...]
    rows JSONB,                         -- [["val1", "val2"], ["val3", "val4"]]
    confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Key-value pairs from forms
CREATE TABLE document_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    field_key TEXT NOT NULL,
    field_value TEXT,
    confidence FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector embeddings for semantic search
CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    page_number INTEGER,
    chunk_index INTEGER DEFAULT 0,
    chunk_text TEXT NOT NULL,
    embedding VECTOR(1536),             -- OpenAI text-embedding-3-small
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable vector similarity search
CREATE INDEX ON document_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

---

## Implementation Approach

### Step 1: Image Preprocessing Pipeline

```python
"""
preprocessing.py - Image preparation for OCR
"""
import cv2
import numpy as np
from pdf2image import convert_from_path
from pathlib import Path
from typing import List, Tuple


def pdf_to_images(pdf_path: str, dpi: int = 300) -> List[np.ndarray]:
    """Convert PDF pages to OpenCV images."""
    pil_images = convert_from_path(pdf_path, dpi=dpi)
    return [np.array(img) for img in pil_images]


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """Full preprocessing pipeline for OCR optimization."""
    # 1. Convert to grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    # 2. Noise reduction (median blur)
    denoised = cv2.medianBlur(gray, 3)

    # 3. Contrast enhancement (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # 4. Adaptive thresholding (binarization)
    binary = cv2.adaptiveThreshold(
        enhanced, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # 5. Deskew
    deskewed = deskew_image(binary)

    return deskewed


def deskew_image(image: np.ndarray) -> np.ndarray:
    """Correct image rotation/skew."""
    coords = np.column_stack(np.where(image > 0))
    if len(coords) < 10:
        return image

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) < 0.5:  # Skip near-zero rotation
        return image

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )
    return rotated


def detect_document_type(image: np.ndarray) -> str:
    """Classify document type based on visual features."""
    # Simple heuristic: check for table-like grid lines
    edges = cv2.Canny(image, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100,
                            minLineLength=100, maxLineGap=10)

    horizontal = 0
    vertical = 0
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y2 - y1) < 10:  # Horizontal
                horizontal += 1
            elif abs(x2 - x1) < 10:  # Vertical
                vertical += 1

    if horizontal > 5 and vertical > 3:
        return 'table_form'  # Route to Textract
    else:
        return 'printed_text'  # Route to Tesseract
```

### Step 2: OCR Extraction

```python
"""
ocr_engines.py - OCR extraction using Tesseract and AWS Textract
"""
import pytesseract
import boto3
import json
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class OCRResult:
    text: str
    confidence: float
    words: List[dict]
    tables: List[dict]
    key_values: List[dict]
    engine: str
    processing_time_ms: int


def extract_with_tesseract(image) -> OCRResult:
    """Extract text using local Tesseract engine."""
    import time
    start = time.time()

    # Get detailed word-level data
    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
        config='--oem 3 --psm 6'  # LSTM engine, uniform text block
    )

    words = []
    confidences = []
    text_parts = []

    for i in range(len(data['text'])):
        word = data['text'][i].strip()
        conf = int(data['conf'][i])

        if word and conf > 0:
            words.append({
                'text': word,
                'confidence': conf / 100.0,
                'bbox': {
                    'left': data['left'][i],
                    'top': data['top'][i],
                    'width': data['width'][i],
                    'height': data['height'][i]
                }
            })
            if conf > 30:  # Include even medium-confidence words in text
                text_parts.append(word)
                confidences.append(conf / 100.0)

    elapsed_ms = int((time.time() - start) * 1000)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    return OCRResult(
        text=' '.join(text_parts),
        confidence=avg_confidence,
        words=words,
        tables=[],       # Tesseract does not extract tables
        key_values=[],    # Tesseract does not extract key-value pairs
        engine='tesseract',
        processing_time_ms=elapsed_ms
    )


def extract_with_textract(document_bytes: bytes,
                          features: List[str] = None) -> OCRResult:
    """Extract text, tables, and forms using AWS Textract."""
    import time
    start = time.time()

    textract = boto3.client('textract', region_name='us-west-2')

    if features is None:
        features = ['TABLES', 'FORMS']

    response = textract.analyze_document(
        Document={'Bytes': document_bytes},
        FeatureTypes=features
    )

    # Parse blocks
    blocks = response['Blocks']
    text_parts = []
    words = []
    tables = []
    key_values = []

    # Build block ID lookup
    block_map = {b['Id']: b for b in blocks}

    for block in blocks:
        if block['BlockType'] == 'WORD':
            words.append({
                'text': block['Text'],
                'confidence': block['Confidence'] / 100.0,
                'bbox': block['Geometry']['BoundingBox']
            })

        elif block['BlockType'] == 'LINE':
            text_parts.append(block['Text'])

        elif block['BlockType'] == 'TABLE':
            table = parse_textract_table(block, block_map)
            tables.append(table)

        elif block['BlockType'] == 'KEY_VALUE_SET':
            if 'KEY' in block.get('EntityTypes', []):
                kv = parse_textract_key_value(block, block_map)
                if kv:
                    key_values.append(kv)

    elapsed_ms = int((time.time() - start) * 1000)
    avg_conf = (sum(w['confidence'] for w in words) / len(words)) if words else 0.0

    return OCRResult(
        text='\n'.join(text_parts),
        confidence=avg_conf,
        words=words,
        tables=tables,
        key_values=key_values,
        engine='textract',
        processing_time_ms=elapsed_ms
    )


def parse_textract_table(table_block: dict, block_map: dict) -> dict:
    """Parse a Textract TABLE block into structured rows/columns."""
    rows = {}
    for relationship in table_block.get('Relationships', []):
        if relationship['Type'] == 'CHILD':
            for cell_id in relationship['Ids']:
                cell = block_map.get(cell_id, {})
                if cell.get('BlockType') == 'CELL':
                    row_idx = cell['RowIndex']
                    col_idx = cell['ColumnIndex']
                    cell_text = get_text_from_block(cell, block_map)
                    if row_idx not in rows:
                        rows[row_idx] = {}
                    rows[row_idx][col_idx] = cell_text

    # Convert to list of lists
    max_row = max(rows.keys()) if rows else 0
    max_col = max(
        max(cols.keys()) for cols in rows.values()
    ) if rows else 0

    result_rows = []
    for r in range(1, max_row + 1):
        row = []
        for c in range(1, max_col + 1):
            row.append(rows.get(r, {}).get(c, ''))
        result_rows.append(row)

    return {
        'row_count': max_row,
        'column_count': max_col,
        'headers': result_rows[0] if result_rows else [],
        'rows': result_rows[1:] if len(result_rows) > 1 else [],
        'confidence': table_block.get('Confidence', 0) / 100.0
    }


def parse_textract_key_value(key_block: dict, block_map: dict) -> Optional[dict]:
    """Parse a KEY_VALUE_SET pair from Textract."""
    key_text = get_text_from_block(key_block, block_map)

    value_text = ''
    for rel in key_block.get('Relationships', []):
        if rel['Type'] == 'VALUE':
            for val_id in rel['Ids']:
                value_block = block_map.get(val_id, {})
                value_text = get_text_from_block(value_block, block_map)

    if key_text:
        return {
            'key': key_text,
            'value': value_text,
            'confidence': key_block.get('Confidence', 0) / 100.0
        }
    return None


def get_text_from_block(block: dict, block_map: dict) -> str:
    """Recursively get text from a block and its children."""
    text_parts = []
    for rel in block.get('Relationships', []):
        if rel['Type'] == 'CHILD':
            for child_id in rel['Ids']:
                child = block_map.get(child_id, {})
                if child.get('BlockType') == 'WORD':
                    text_parts.append(child['Text'])
    return ' '.join(text_parts)
```

### Step 3: Confidence Scoring & Quality Assessment

```python
"""
confidence.py - Document quality assessment
"""
from dataclasses import dataclass


@dataclass
class QualityReport:
    overall_confidence: float
    total_words: int
    low_confidence_words: int
    high_confidence_words: int
    quality_grade: str            # A, B, C, D, F
    needs_review: bool
    issues: list


CONFIDENCE_THRESHOLD = 0.70   # Below this = low confidence word
REVIEW_THRESHOLD = 0.80       # Below this overall = flag for review
REJECT_THRESHOLD = 0.50       # Below this = reject/re-scan


def assess_quality(ocr_result) -> QualityReport:
    """Assess OCR extraction quality and determine if review is needed."""
    words = ocr_result.words
    total = len(words)
    issues = []

    if total == 0:
        return QualityReport(
            overall_confidence=0.0, total_words=0,
            low_confidence_words=0, high_confidence_words=0,
            quality_grade='F', needs_review=True,
            issues=['No text extracted from document']
        )

    low_conf = sum(1 for w in words if w['confidence'] < CONFIDENCE_THRESHOLD)
    high_conf = sum(1 for w in words if w['confidence'] >= 0.90)
    avg_conf = sum(w['confidence'] for w in words) / total

    # Determine grade
    if avg_conf >= 0.95:
        grade = 'A'
    elif avg_conf >= 0.85:
        grade = 'B'
    elif avg_conf >= 0.70:
        grade = 'C'
    elif avg_conf >= 0.50:
        grade = 'D'
    else:
        grade = 'F'

    # Identify issues
    low_conf_pct = low_conf / total * 100
    if low_conf_pct > 20:
        issues.append(f'{low_conf_pct:.0f}% of words have low confidence - possible scan quality issue')
    if avg_conf < REVIEW_THRESHOLD:
        issues.append(f'Overall confidence {avg_conf:.0%} below review threshold')
    if total < 10:
        issues.append('Very few words extracted - possible blank page or image issue')

    needs_review = avg_conf < REVIEW_THRESHOLD or low_conf_pct > 30

    return QualityReport(
        overall_confidence=avg_conf,
        total_words=total,
        low_confidence_words=low_conf,
        high_confidence_words=high_conf,
        quality_grade=grade,
        needs_review=needs_review,
        issues=issues
    )
```

### Step 4: Knowledge Base Integration

```python
"""
storage.py - Store OCR results in Supabase knowledge base
"""
import openai
from supabase import create_client
from typing import List


supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)


def store_document(filename: str, file_path: str,
                   pages: list, document_type: str,
                   overall_confidence: float,
                   contact_id: int = None) -> str:
    """Store a processed document and all its extracted data."""

    # 1. Create document record
    doc = supabase.table('documents').insert({
        'filename': filename,
        'file_path': file_path,
        'document_type': document_type,
        'page_count': len(pages),
        'ocr_engine': pages[0].engine if pages else 'unknown',
        'overall_confidence': overall_confidence,
        'status': 'completed',
        'nutshell_contact_id': contact_id
    }).execute()

    doc_id = doc.data[0]['id']

    # 2. Store page-level text
    for i, page_result in enumerate(pages):
        supabase.table('document_pages').insert({
            'document_id': doc_id,
            'page_number': i + 1,
            'raw_text': page_result.text,
            'confidence': page_result.confidence,
            'word_count': len(page_result.words),
            'low_confidence_words': sum(
                1 for w in page_result.words
                if w['confidence'] < 0.70
            ),
            'ocr_engine': page_result.engine,
            'processing_time_ms': page_result.processing_time_ms
        }).execute()

        # 3. Store tables
        for t_idx, table in enumerate(page_result.tables):
            supabase.table('document_tables').insert({
                'document_id': doc_id,
                'page_number': i + 1,
                'table_index': t_idx,
                'row_count': table['row_count'],
                'column_count': table['column_count'],
                'headers': table['headers'],
                'rows': table['rows'],
                'confidence': table['confidence']
            }).execute()

        # 4. Store key-value pairs
        for kv in page_result.key_values:
            supabase.table('document_fields').insert({
                'document_id': doc_id,
                'page_number': i + 1,
                'field_key': kv['key'],
                'field_value': kv['value'],
                'confidence': kv['confidence']
            }).execute()

    # 5. Generate and store vector embeddings
    store_embeddings(doc_id, pages)

    return doc_id


def store_embeddings(doc_id: str, pages: list,
                     chunk_size: int = 500):
    """Chunk text and store vector embeddings for semantic search."""
    for i, page in enumerate(pages):
        text = page.text
        if not text.strip():
            continue

        # Split into chunks
        words = text.split()
        chunks = []
        for j in range(0, len(words), chunk_size):
            chunk = ' '.join(words[j:j + chunk_size])
            chunks.append(chunk)

        for c_idx, chunk in enumerate(chunks):
            # Generate embedding
            response = openai_client.embeddings.create(
                model='text-embedding-3-small',
                input=chunk
            )
            embedding = response.data[0].embedding

            supabase.table('document_embeddings').insert({
                'document_id': doc_id,
                'page_number': i + 1,
                'chunk_index': c_idx,
                'chunk_text': chunk,
                'embedding': embedding
            }).execute()


def semantic_search(query: str, limit: int = 5) -> List[dict]:
    """Search documents using semantic similarity."""
    # Generate query embedding
    response = openai_client.embeddings.create(
        model='text-embedding-3-small',
        input=query
    )
    query_embedding = response.data[0].embedding

    # Search using pgvector cosine similarity
    results = supabase.rpc('match_documents', {
        'query_embedding': query_embedding,
        'match_threshold': 0.7,
        'match_count': limit
    }).execute()

    return results.data
```

### Step 5: n8n Workflow Orchestration

```
Workflow: Document Processing Pipeline

[Webhook Trigger: File uploaded to Supabase Storage]
    |
    v
[HTTP Request: Download file from Supabase Storage]
    |
    v
[Code Node: PDF to Images]
    - Use pdf2image to convert pages
    - Store temporary image files
    |
    v
[Code Node: Preprocess + Classify]
    - Run preprocessing pipeline
    - Detect document type (table_form vs printed_text)
    |
    v
[Switch Node: Route by document type]
    |
    +-- printed_text --> [Code Node: Tesseract OCR]
    |                       |
    +-- table_form  --> [HTTP Request: AWS Textract]
    |                       |
    +-- handwritten --> [HTTP Request: AWS Textract]
    |
    v (merge results)
[Code Node: Confidence Assessment]
    |
    v
[IF Node: Confidence > 0.50?]
    |-- YES --> [Code Node: Store in Supabase]
    |               |
    |               v
    |           [Code Node: Generate Embeddings]
    |               |
    |               v
    |           [HTTP Request: Update Nutshell CRM]
    |
    |-- NO  --> [Notification: Flag for manual review]
                    |
                    v
                [Slack/Email: "Low quality OCR - needs re-scan"]
```

---

## Cost Implications

### Per-Document Processing Costs

| Step | Cost | Notes |
|------|------|-------|
| PDF Conversion | $0 | Local (pdf2image) |
| Image Preprocessing | $0 | Local (OpenCV) |
| Tesseract OCR | $0 | Open source, local |
| AWS Textract (if needed) | $0.015-0.065/page | Tables+Forms |
| OpenAI Embeddings | ~$0.0001/page | text-embedding-3-small |
| Supabase Storage | ~$0.02/GB/month | Negligible for text |

### Monthly Cost Projection (250 pages/month)

| Component | Calculation | Monthly Cost |
|-----------|------------|-------------|
| Tesseract (150 pages) | Free | $0.00 |
| Textract (100 pages, tables+forms) | 100 x $0.065 | $6.50 |
| OpenAI Embeddings (250 pages) | 250 x $0.0001 | $0.03 |
| Supabase Storage | ~0.01 GB | $0.00 |
| **Total** | | **~$6.53/month** |

---

## Estimated Build Hours

| Phase | Tasks | Hours |
|-------|-------|-------|
| Environment Setup | Install Tesseract, Poppler, OpenCV on Mac Mini | 2-3 |
| Preprocessing Pipeline | Grayscale, denoise, deskew, binarize, classify | 6-8 |
| Tesseract Integration | pytesseract wrapper, word-level extraction | 3-4 |
| Textract Integration | boto3 setup, table/form parsing, async handling | 6-8 |
| Confidence Scoring | Quality assessment, grade assignment, review flags | 3-4 |
| Supabase Schema + Storage | Tables, indexes, storage functions | 3-4 |
| Vector Embeddings | Chunking, OpenAI embeddings, pgvector search | 4-6 |
| n8n Workflow | Pipeline orchestration, routing, error handling | 4-6 |
| CRM Integration | Link documents to Nutshell contacts/leads | 2-3 |
| Testing & QA | Sample documents, edge cases, quality validation | 6-8 |
| **Total** | | **39-54 hours** |

### Prerequisites
- [ ] Mac Mini with Python 3.10+, Tesseract 5.x, Poppler, OpenCV
- [ ] AWS account with Textract access and IAM credentials
- [ ] OpenAI API key for embeddings
- [ ] Supabase project with pgvector extension enabled
- [ ] n8n instance with Code node and HTTP Request capability
- [ ] Sample documents (5-10 each of contracts, invoices, handwritten)

### Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Poor scan quality | Low OCR accuracy | Preprocessing pipeline + confidence scoring |
| Textract API costs spike | Unexpected bills | Route clean docs to free Tesseract first |
| Large PDF documents | Slow processing | Async processing, page-level parallelism |
| Table structure errors | Incorrect data extraction | Confidence thresholds + manual review queue |
| Embedding costs at scale | Growing API costs | Batch embeddings, cache common documents |

---

## References

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [pytesseract](https://pypi.org/project/pytesseract/)
- [OpenCV Python](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [pdf2image](https://pypi.org/project/pdf2image/)
- [AWS Textract boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/textract.html)
- [Supabase pgvector](https://supabase.com/docs/guides/ai/vector-columns)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [OCR Pipeline Best Practices (Medium)](https://hypotenuselabs.medium.com/an-ocr-pipeline-for-machine-learning-the-good-the-bad-and-the-ugly-9ae751314ce6)

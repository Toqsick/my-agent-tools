---
name: pdf
description: >-
  Use when user asks for reading or extracting text from PDFs, merging or splitting PDF files, extracting PDF tables, or running OCR on scanned pages. NOT for editing wording in an existing PDF or converting a document to EPUB. Selects appropriate Python or CLI tooling for PDF inspection, extraction, table handling, page operations, and OCR workflows.
license: Proprietary
metadata:
  author: anthropics
  version: 1.0
lane: worker-flash
reasoning_effort: high
agent: Writer
routing_hint: '**Agent-Scope:** Long-form content, docs, proposals, copy. Off-scope:
  code, design, data modeling — return to Yuno.


  Routing-Spec: `yuno-team-routing`.

  '
author: Hermes Agent
version: 1.0.0
trigger_keywords: ['pdf', 'extracting', 'ocr', 'reading', 'text']
keywords: ['extracting', 'user', 'asks', 'reading', 'text']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['ocr-and-documents', 'nano-pdf', 'epub-export']
---

---


# PDF Processing Guide

Umfassender Guide für PDF-Verarbeitung mit Python und CLI-Tools.

## Quick Start

```python
from pypdf import PdfReader, PdfWriter

# PDF lesen
reader = PdfReader("document.pdf")
print(f"Seiten: {len(reader.pages)}")

# Text extrahieren
text = ""
for page in reader.pages:
    text += page.extract_text()
```

set -euo pipefail
## Python Libraries

### pypdf — Basis-Operationen
- Lesen, Schreiben, Zusammenführen, Splitten
- Text-Extraktion, Metadaten

### pdfplumber — Tabellen-Extraktion
```python
import pdfplumber
with pdfplumber.open("doc.pdf") as pdf:
    for page in pdf.pages:
        tables = page.extract_tables()
```

set -euo pipefail
### pytesseract — OCR für gescannte PDFs
```python
# OCR auf PDF-Seiten
from pdf2image import convert_from_path
images = convert_from_path("scan.pdf")
for img in images:
    text = pytesseract.image_to_string(img, lang="deu")
```

set -euo pipefail
## CLI-Tools

```bash
# PDFs zusammenführen
pdfunite file1.pdf file2.pdf merged.pdf

# PDF splitten
pdftk input.pdf burst

# Text extrahieren
pdftotext input.pdf output.txt

# OCR (mit ocrmypdf)
ocrmypdf input.pdf output.pdf --language deu
```

## Hinweis für Hermes

Die Anthropic-PDF-Skills sind auf Claude Code zugeschnitten. Für Hermes nutze die eingebauten Tools:
- `ocr-and-documents` Skill für Text-Extraktion
- `nano-pdf` Skill für PDF-Bearbeitung
- `pymupdf` und `marker-pdf` als Python-Alternativen

# pdf (Anthropic) — Skill-Beschreibung

**Name:** pdf
**Version:** 1.0.0
**Autor:** Anthropic
**Quelle:** https://github.com/anthropics/skills
**Installs:** 100K+ (Anthropic offiziell)
**Lizenz:** Proprietary (siehe LICENSE.txt)

## Was ist das?

Offizieller PDF-Processing-Skill von Anthropic. Deckt alle gängigen PDF-Operationen ab: Lesen, Extrahieren, Zusammenführen, Splitten, Rotieren, Wasserzeichen, Formulare ausfüllen, Verschlüsseln, OCR.

## Wann nutzen?

- PDF-Dateien lesen oder Text/Tabellen extrahieren
- Mehrere PDFs zusammenführen oder splitten
- PDF-Seiten rotieren
- Wasserzeichen hinzufügen
- Neue PDFs erstellen
- PDF-Formulare ausfüllen
- PDFs verschlüsseln/entschlüsseln
- OCR auf gescannte PDFs anwenden
- Bilder aus PDFs extrahieren

## Unterstützte Operationen

| Operation | Tool |
|-----------|------|
| PDF lesen | pypdf (PdfReader) |
| Text extrahieren | pypdf, pdfplumber |
| Tabellen extrahieren | pdfplumber |
| PDFs zusammenführen | pypdf (PdfWriter) |
| PDF splitten | pypdf |
| Seiten rotieren | pypdf |
| Wasserzeichen | pypdf |
| Formulare ausfüllen | pypdf |
| Verschlüsseln | pypdf |
| OCR | pytesseract + pdf2image |
| CLI-Tools | pdftk, pdfunite, pdftotext, ocrmypdf |

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

# PDFs zusammenführen
writer = PdfWriter()
for pdf_file in ["file1.pdf", "file2.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)
with open("merged.pdf", "wb") as f:
    writer.write(f)
```

## OCR für gescannte PDFs

```python
from pdf2image import convert_from_path
import pytesseract

images = convert_from_path("scan.pdf")
for img in images:
    text = pytesseract.image_to_string(img, lang="deu")
```

## CLI-Tools

```bash
# PDFs zusammenführen
pdfunite file1.pdf file2.pdf merged.pdf

# PDF splitten
pdftk input.pdf burst

# Text extrahieren
pdftotext input.pdf output.txt

# OCR
ocrmypdf input.pdf output.pdf --language deu
```

## Hinweis für Hermes

Das Anthropic-PDF-Skill ist auf Claude Code zugeschnitten. Für Hermes gibt es bereits:
- `ocr-and-documents` Skill für Text-Extraktion aus PDFs/Scans
- `nano-pdf` Skill für PDF-Bearbeitung (Text/Titel korrigieren)
- `pymupdf` und `marker-pdf` als Python-Alternativen

Das Anthropic-Skill kann als Referenz für erweiterte PDF-Operationen dienen.

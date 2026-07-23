# CSV-Encoding Edge-Cases — Discovered 2026-07-15

## Purpose

Document ALL known CSV encoding edge-cases that break bulk-import tools (Canva, TikTok, etc.)
and the validation patterns that catch them. These were discovered iteratively across multiple
skill-polish sessions and affect ANY CSV-generating or CSV-consuming Hermes skill.

## Quick Reference

| Edge-Case | Symptom | Root Cause | Detection | Fix |
|---|---|---|---|---|
| **UTF-8 BOM** (`\ufeff` at byte 0) | Header[0] = "`\ufeffpost_id`" (8 chars) — silent field mismatch | Excel exports add BOM on "UTF-8" save | `raw.startswith(b'\xef\xbb\xbf')` or use `utf-8-sig` decode | `open(path, encoding="utf-8-sig")` |
| **LATIN-1/ISO-8859-1** | Umlauts survive ASCII-check, Canva import corrupts | Windows/Excel export not UTF-8 | Compare `len(ascii_decoded)` vs `len(raw)` | Convert to UTF-8; warn user about Excel encoding |
| **Naked Umlauts (äöüß)** | Canva bulk-create silently degrades | File IS UTF-8 but card text has raw umlauts | Regex/Literal search for `[äöüßÄÖÜ]` | Replace: ä→ae, ö→oe, ü→ue, ß→ss |
| **Empty Pitch Column** | Canva silently skips slide 8 | CSV row has `,,` instead of `,pitch_text,` | Python csv.reader: check `row[pitch_col] == ""` | Always fill pitch from rotation pool |
| **Quoted Fields with Commas** | awk -F',' counts 13+ cols instead of 11 | `"Caption, mit Komma"` has embedded comma | Always use Python `csv` module, NEVER `awk -F','` | — |
| **Multi-line / Embedded Newlines** | csv.reader splits rows at embedded newline | `"Card text\nwith line break"` in quoted field | `csv.reader` with `newline=""` parameter | `open(path, newline="")` |
| **Inconsistent Row Widths** | Some rows have 10 cols, some 12, some 11 | Human-edited CSV, copy-paste errors | Check `len(row)` per row vs `len(header)` | Flag `{width: count}` distribution |
| **CRLF Line Endings** | Windows-style, transparent to csv module | — | No detection needed | — |
| **Empty File (0 bytes)** | csv.reader loops silently, no error | Truncated download, failed generation | `file.stat().st_size == 0` before any read | Error: "Datei ist leer" |
| **Header-Only CSV** | csv.reader yields 0 data rows | Template saved before data was added | Check `len(rows)` < 1 after `next(reader)` | Error: "CSV hat nur Header" |
| **Very Long Rows (10K+ chars)** | No perf issue (tested) | — | — | Verified: OK |
| **Large CSVs (500+ rows)** | <50ms validation (tested) | — | — | Verified: OK |
| **Symlinked Files** | `Path.exists()` follows symlinks | — | — | Verified: OK |

## Side-by-Side: Awk vs Python csv Module

| Criterion | `awk -F','` | Python `csv` module |
|---|---|---|
| Quoted-field safe | ❌ — counts commas inside quotes | ✅ — RFC 4180 compliant |
| Multi-line fields | ❌ — newline = new row | ✅ — with `newline=""` |
| Row-width detection | ❌ — `NF` not exposed per row | ✅ — `len(row)` per row |
| Empty-field detection | ⚠️ — `$i == ""` works | ✅ — `row[i] == ""` |
| BOM handling | ❌ — first field starts with `\ufeff` | ✅ — `encoding="utf-8-sig"` |
| Per-row error messages | ❌ — batch mode exit code | ✅ — per-row warnings + aggregate |
| Exit-code reliability | ❌ — piped through `tail` masks exit | ✅ — correct exit 0/1 |

**Decision:** Always use Python `csv` module for CSV validation. Awk is only suitable for quick manual inspection.

## How Encoding Detection Works (Best Practice)

```python
from pathlib import Path

def detect_encoding(path: Path) -> dict:
    """Returns encoding diagnosis for a CSV file."""
    raw = path.read_bytes()
    result = {"size": len(raw), "bom": False, "encoding": "unknown",
              "naked_umlauts": False, "ascii_safe": False}

    # BOM check
    if raw.startswith(b'\xef\xbb\xbf'):
        result["bom"] = True
        raw_clean = raw[3:]
    else:
        raw_clean = raw

    # UTF-8 decode test
    try:
        raw_clean.decode("utf-8")
        result["encoding"] = "utf-8"
    except UnicodeDecodeError:
        raw_clean.decode("latin-1")
        result["encoding"] = "latin-1"

    # ASCII safety check (naked umlauts = dangerous)
    ascii_len = len(raw_clean.decode("ascii", errors="ignore"))
    result["ascii_safe"] = (ascii_len == len(raw_clean))

    # Naked umlauts (äöüß in card text)
    text = raw_clean.decode(result["encoding"] if result["encoding"] != "unknown" else "utf-8", errors="replace")
    for char in "äöüßÄÖÜ":
        if char in text:
            result["naked_umlauts"] = True
            break

    return result
```

## Pitfalls

- **LATIN-1 + ASCII-check blind spot:** `raw.decode("ascii", errors="ignore")` strips umlauts silently. A LATIN-1 file with umlauts PASSES the ASCII-check because the stripped result looks clean. **Fix:** Compare the length of the stripped decode against `len(raw)`. If ascii_len < len(raw), there are non-ASCII bytes.
- **BOM-only LATIN-1 trap:** A file with BOM header (3 bytes `ef bb bf`) but LATIN-1 body. The BOM is valid UTF-8, the body isn't. Solution: try `utf-8-sig` first; if that fails, try `latin-1` without BOM.
- **Empty file caught by csv.reader:** `csv.reader` loops silently over empty files — no error. You stay in a "processing" loop that terminates without output. Always size-check before opening.
- **csv module pipe fail:** `tail -n +2 | csv.reader` loses the original exit code. Read file directly, don't pipe.

## History

- **2026-07-15 v0.4.0:** All edge-cases above documented after 30-check self-test. 4 real production bugs found via these patterns: empty pitch, row-width drift, BOM header corruption, pitch-schema asymmetry.
- **2026-07-15 validate_script.py:** Same BOM fix applied (utf-8 → utf-8-sig) in 2 additional skills (media/beat-sync-editor, creative/video/validate_script.py).
- **Previous:** BOM bug first identified in tiktok-design-assistant v0.1.0→v0.2.0 migration.
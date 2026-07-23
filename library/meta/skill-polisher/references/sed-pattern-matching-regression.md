# Sed-Pattern-Matching-Regression: Zwei-Klassen-Ersetzung

> **Validierung:** 2026-07-16, Skill-Polish-Runde 2
> **Betroffen:** `meta/skill-polisher/scripts/skill_polisher.py`
> **Fix-Zeit:** ~30 Sekunden Revert + Verify
> **Lektion:** `sed` hat keine Semantik — es ersetzt blind Text.

## Problem

Ein `sed -i 's/encoding="utf-8"/encoding="utf-8-sig"/g'` auf `skill_polisher.py`
ersetzte **alle** Vorkommen, auch in:

```python
# Zeile 87: Pattern-Matching-String (SUCHT nach utf-8)
if re.search(r'read_text\(\s*encoding="utf-8"', text):
    bom_files.append(py)
```

Das war KEIN Read-Call — es war ein **Such-Pattern** der sagt "finde Zeilen mit encoding=utf-8".
Nach dem sed suchte der Pattern nach `utf-8-sig` — also nach dem was bereits gefixed war —
und fand nichts mehr.

**Drei Klassen von encoding="utf-8" im Code:**

| Klasse | Beispiel | Soll ersetzt werden? |
|--------|----------|:--------------------:|
| **Read-Call** | `path.read_text(encoding="utf-8")` | ✅ Ja — das liest Files |
| **Write-Call** | `path.write_text(text, encoding="utf-8")` | ⚠️ Optional — writes sind BOM-unabhaengig |
| **Pattern-Matching** | `re.search(r'encoding="utf-8"', text)` | ❌ **Nein** — das ist ein Such-Pattern |

## Fix (validiert)

**Schlecht (zerstoert Such-Strings):**
```bash
sed -i 's/encoding="utf-8"/encoding="utf-8-sig"/g' script.py
```

**Gut (Python-Sting-Patching mit Kontext-Pruefung):**
```python
from pathlib import Path
import re

def fix_bom_reads(filepath: Path) -> bool:
    """Ersetze NUR read_text(encoding='utf-8') — NICHT in Pattern-Strings."""
    text = filepath.read_text()
    modified = False
    
    def safe_replace(m: re.Match) -> str:
        """Ersetze nur wenn es ein Read-Call ist, kein Pattern-String."""
        full_pre = text[max(0, m.start()-60):m.start()]
        # Prufe ob es sich um einen Such-Pattern (re.search/re.match) handelt
        if re.search(r'(re\.search|re\.match|re\.findall|in\s+text)', full_pre):
            return m.group(0)  # NICHT ersetzen — ist ein Such-Pattern
        return 'encoding="utf-8-sig"'
    
    new_text = re.sub(r'encoding="utf-8"', safe_replace, text)
    if new_text != text:
        filepath.write_text(new_text)
        return True
    return False
```

## Guard-Checklist (vor jedem Batch-Replace)

1. `grep -n '<pattern>' <file>` — zeige ALLE Vorkommen
2. Manuell prufen: jedes Vorkommen = Read-Call oder Pattern-String?
3. Wenn beides: **sed verboten** — Python-String-Patching mit Kontext-Pruefung
4. Wenn nur Read-Calls: `sed` ist in Ordnung, ABER vorher Backup:
   ```bash
   cp file.py file.py.bak.$(date +%Y%m%d)
   ```
5. Nach Replace: `grep -n '<neuer-wert>' <file>` — Vorkommen mit Kontext prufen
6. Syntax-Check: `python3 -m py_compile file.py`

## Faustregel

> **Wenn du Code bearbeitest der STRINGS enthaelt die nach Text MUSTERN suchen,
> darfst du NIEMALS blind `sed` auf diese Muster loslassen.**
> 
> Sed weiss nicht ob `encoding="utf-8"` ein Befehl ist (lies mit diesem Encoding)
> oder ein Muster (suche nach diesem Encoding-String). Das ist Kontext-Wissen,
> das nur Python (oder du selbst) hat.

## Fallbeispiel

```
Vor sed:
  read_text(encoding="utf-8")       → Read-Call (soll nach utf-8-sig)
  re.search(r'encoding="utf-8"', t) → Pattern-String (darf bleiben)
  write_text(text, encoding="utf-8") → Write-Call (kann bleiben, utf-8 ist OK)

Nach sed (blind):
  read_text(encoding="utf-8-sig")    → ✅ Richtig
  re.search(r'encoding="utf-8-sig"', t) → ❌ FALSCH — sucht jetzt nach utf-8-sig
  write_text(text, encoding="utf-8-sig") → ⚠️ Optionale Aenderung
```

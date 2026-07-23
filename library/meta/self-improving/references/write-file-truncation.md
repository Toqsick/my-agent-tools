# write_file Silent Truncation — Tool Quirk & Workaround

**Entdeckt:** 2026-07-14 (Sub-Bee Cross-Verification Session)
**Kategorie:** tool-quirk
**Status:** verified

## Symptom

`write_file(content="...")` mit längerem Inhalt (~1100+ Zeichen) **truncated den Content still** — kein Fehler, keine Warnung, keine Exception. Die Datei wird erstellt, enthält aber nur die ersten ~1000–1100 Zeichen des übergebenen Inhalts. Der Rest geht verloren.

### Beispiel

```python
# Angenommen report_content ist 3500 Zeichen lang
write_file(path="/tmp/report.md", content=report_content)
# → Datei existiert, ist aber NUR 1100 Zeichen groß
# → Kein Fehler, kein Hinweis auf Truncation
```

## Root Cause

Das `content`-Parameter-Feld des `write_file`-Tools unterliegt einer **impliziten Input-Längenbegrenzung** (vermutlich auf Tool-Definitionsebene oder im Serialisierungs-Format). Content jenseits dieser Schwelle wird beim Tool-Aufruf abgeschnitten, bevor es die File-Write-Routine erreicht. Der Schreibvorgang selbst funktioniert fehlerfrei — er schreibt nur, was ankam.

Die Schwelle liegt bei etwa **1000–1200 Zeichen** — nicht gemessen, aber empirisch beobachtet bei zwei unabhängigen Versuchen mit ~1100 Zeichen langem Inhalt.

## Workaround: Chunked Write via Terminal + Append + Patch

Bei Inhalten >1000 Zeichen: **niemals** auf einen einzelnen `write_file`-Call vertrauen. Stattdessen eine **Chunked-Write-Strategie** verwenden:

### Strategie A: Initial Write (klein halten) + Append per Terminal

```python
# 1. Kleinen initialen Inhalt mit write_file schreiben (<800 Zeichen)
write_file(path="/tmp/output.md", content="# Überschrift\n\nEinleitung...")

# 2. Rest in Häppchen per terminal anhängen
terminal(command="""printf '%s\\n' \
  '| Spalte A | Spalte B |' \
  '|----------|----------|' \
  '| Wert 1   | Wert 2   |' \
  '| Wert 3   | Wert 4   |' \
  >> /tmp/output.md && echo "appended chunk A" && wc -l /tmp/output.md
""")
```

### Strategie B: Umweg über Datei + Chunked Append

Bei vielen Zeilen die nicht in einen Befehl passen:

```python
# 1. Chunk 1 schreiben
terminal(command="""printf '%s\\n' <zeile1> <zeile2> ... <zeileN> > /tmp/output.md""")
# 2. Chunk 2 anhängen
terminal(command="""printf '%s\\n' <zeileN+1> ... <zeileM> >> /tmp/output.md""")
# 3. Nach jedem Append: wc -l zum Verifizieren
# 4. Final cleanup mit patch falls nötig
patch(mode="replace", path="/tmp/output.md", old_string="<duplikat>", new_string="")
```

### Strategie C: Python im Terminal (für strukturierte Inhalte)

```python
# Komplette File-Generierung via Python stdin-Heredoc:
terminal(command="""python3 -c "
content = open('/dev/stdin').read()
with open('/tmp/output.md', 'w') as f:
    f.write(content)
" << 'PYEOF'
<kompletter Inhalt hier>
PYEOF
""")
```

**Achtung:** Heredoc (`<< 'PYEOF'`) kann bei >2–3 KB ebenfalls truncaten — auf Strategie A/B ausweichen.

## Guard: Immer File-Größe verifizieren

Nach jedem `write_file` mit längeren Inhalten:

```python
# Content-Länge vorher merken
content_length = len(report_content)  # z.B. 3500
# Nach write_file prüfen
terminal(command="stat -c%s /tmp/output.md")
# 3500 vs 1100 → Truncation erkannt → Chunked-Strategie
```

## Verwandte Lessons

- Patch `replace_all=true` Tripling (Beispiel 4 in `self-improving` SKILL.md) — ähnliches Muster: Tool-Input-Grenze führt zu stillem Datenverlust
- Wenn Datei-Korruption durch Patch-Fehler entsteht → **immer `write_file` zur kompletten Überschreibung**, nie weiteren Patch riskieren
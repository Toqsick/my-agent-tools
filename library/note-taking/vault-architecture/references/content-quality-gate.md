# Content Quality Gate — Vault Notes

> Grep-basierte Markdown-Qualitätsvalidierung für große Vault-Notes (≥ 100 Zeilen).
> Ergänzt den `anti-ai-tells-daily-notes.md` (Daily-Notes-Stil) und `obsidian-vault-quality-audit` (Struktur-Audit bestehender Notes).
> **Präventiv**: Qualität erzwingen, während die Note geschrieben wird, nicht erst nachträglich.

## Wann anwenden

- Du schreibst eine neue Vault-Note mit > 100 Zeilen (Cookbook, Guide, System-Doku, MOC-erweiterung)
- Die Note soll mehrere Quellen konsolidieren (Wiki-Links zu anderen Notes sind Pflicht)
- Die Note wird von Basti gelesen werden (Quality-Standard muss sichtbar sein)
- **Nicht für**: Daily Notes (→ `anti-ai-tells-daily-notes.md`), Quick-Capture im Inbox-Format, temporäre Scratch-Notes

## Qualitätskriterien

| Kriterium | Zielwert | Warum |
|---|---|---|
| **Em-Dashes (`—`)** | 0 | Em-Dash-heavy ist ein AI-Tell; Semikolon/Punkt/Doppelpunkt stattdessen |
| **Inline-Header (`^- **`)** | 0 | `- **Label:** text` = Bullet-List als Header-Ersatz → schreibt natürlicher |
| **Mid-sentence Boldface** | 0 | Boldface nur in Headern, Lead-Labels, Tabellen — nie im Satzfluss |
| **Wiki-Links (unique)** | ≥ 5 | Vernetzung ist Vault-DNA; 5+ Outgoing belegen Relevanz |
| **Boldface gesamt** | angemessen | Strukturell nötige Boldfaces (Headern, Tabellen-Heads, Lead-Labels) zählen — kein Mid-Sentence |

## Workflow: Schreiben → Validieren → Fixen → Verifizieren

### 1. Schreiben

Schreibe die Note mit `write_file` vollständig. Achte beim Schreiben bereits auf die Qualitätskriterien — das reduziert Iterationen.

**Checkliste beim Schreiben:**
- [ ] Em-Dashes vermeiden (Bindestrich oder Doppelpunkt statt —)
- [ ] Bullet-Listen als echte Sätze, nicht als `**Label:** text`
- [ ] Boldface nur für echte Headings, Tabellen-Header, und maximal 1 Lead-Label pro Section
- [ ] Wiki-Links zu verwandten Notes einbauen (mindestens 5)
- [ ] `//command:`-Marker für Code-Snippets (wenn GreyScript)

### 2. Validieren (Grep-Befehle)

Nach dem ersten Schreibdurchlauf die Validierung ausführen:

```bash
F="/path/to/note.md"

echo "=== Em-Dashes (Ziel: 0) ==="
grep -c '—' "$F" || echo "0"

echo "=== Inline-Header (Ziel: 0) ==="
grep -cE '^- \*\*[A-Z]' "$F" || echo "0"

echo "=== Mid-Sentence-Boldface (Ziel: 0) ==="
grep -cE '\w \*\*[A-Za-z]' "$F" || echo "0"

echo "=== Boldface-Count gesamt ==="
grep -oE '\*\*[^*]+\*\*' "$F" | wc -l

echo "=== Wiki-Links (unique) ==="
grep -oE '\[\[[^]]+\]\]' "$F" | sort -u | wc -l

echo "=== Wiki-Links (alle) ==="
grep -cE '\[\[[^]]+\]\]' "$F" || echo "0"
```

### 3. Fixen (Patch-Tool)

Für jedes Kriterium das > 0 ist:

**Em-Dashes**: Jedes `—` durch ` - ` oder `: ` ersetzen. Systematische Ersetzung mit `sed`:

```bash
sed -i 's/ — / - /g; s/—/:/g' "$F"
```

**Inline-Header**: Jedes `^- **`-Pattern umschreiben in echten Satz oder echten Header:

- **`**Label:** text`** → `**Label**: text` (Lead-Label, kein Inline-Header) — OK wenn der Doppelpunkt nach dem Bold schließt, nicht davor
- **`- **Label:** text`** → `Label: text` (Bullet als normaler Satz) — der bevorzugte Fix
- **`- **Label:**` → `**Label**:` (nur wenn es ein Lead-Label ist, kein voller Satz danach)

**Mid-Sentence-Boldface**: Boldface in der Mitte eines Satzes entfernen oder an den Satzanfang ziehen. `**nächste**` → `nächste`, `**nicht**` → `nicht`, `**alle 15**` → `alle 15`.

**Wiki-Links ergänzen**: Wenn < 5 unique, passende Notes aus dem Vault finden und als `[[Note Name]]` einbauen. Mindestens 3 neue Links hinzufügen. Bevorzugte Quellen für gute Links:
- Verwandte System-Doku-Notes
- MOC-Dateien die das Thema berühren
- Toolkit/Patterns/Werkzeugkasten-Notes

### 4. Re-Validieren

Nach jedem Fix-Durchlauf die Grep-Befehle aus Schritt 2 erneut ausführen und bestätigen, dass alle Zielwerte erreicht sind.

**Erst wenn alle Checks durchlaufen, den Report an Basti geben.**

## Häufige Fehler

| Fehler | Erkennung | Fix |
|---|---|---|
| `patch`-Tool feuert `_warning: file was modified since you last read it` | Tool-Output zeigt Warning | `read_file` erneut aufrufen, dann patchen |
| `sed` ersetzt zu viel (Em-Dash in Code-Blöcken) | Grep-Count sinkt nicht wie erwartet | Code-Blöcke vorher in temporäre Datei auslagern |
| `**Wichtig**:` als Lead-Label zählt als Mid-Sentence-Boldface | `grep -cE '\w \*\*[A-Za-z]'` matcht `**: Wichtig**` | `**Wichtig**:` ist OK als Standalone-Label (kein Mid-Sentence) — den Grep-Check nicht auf Lead-Labels anwenden |
| Lead-Label-Pattern (`**: text`) wird fälschlich als Inline-Header gezählt | `grep -cE '^- \*\*[A-Z]'` matcht `**Ziel:**` | Das ist ein Lead-Label, kein Inline-Header — in Ordnung solange es nicht `- **Ziel:** text` ist |
| `grep -c` gibt 0 aus ohne Fehler, aber `|| echo "0"` überschreibt | `grep -c` returned exit 1 wenn keine Matches, also wird `echo "0"` ausgeführt | `|| echo "0"` ist korrekt — zeigt 0 an wenn keine Matches |

## Vergleich mit anderen Quality-Skills

| Skill | Fokus | Wann |
|---|---|---|
| `anti-ai-tells-daily-notes.md` | Stil-Check für Daily Notes (AI-Vokabeln, Negativ-Parallelismus, Fliesssprache) | Täglich nach Daily-Note-Write |
| `content-quality-gate.md` (dieses File) | Struktur-Check für große Content-Notes (Em-Dash, Boldface, Inline-Header, Wiki-Links) | Nach jedem Write einer großen Note |
| `obsidian-vault-quality-audit` (Skill) | Post-hoc Vault-Health (Backlinks, Orphans, Broken Links, Plugin-Drift) | Nach Cluster-Abschluss, periodisch |
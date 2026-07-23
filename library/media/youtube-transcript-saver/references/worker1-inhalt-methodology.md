# Worker-1-Methodik: Inhalt + Satzzeichen + Minuten-Marker

## Wann einsetzen

Worker 1 (Inhalt) ist der erste parallele Worker in **Stufe 3** der Caption-Polishing-Pipeline.
Er läuft **parallel** zu Worker 2 (Stil/Eigennamen) und Worker 3 (Faktencheck) und wird erst nach Fertigstellung aller drei Worker durch den Merger zusammengeführt.

**Seine Aufgabe:** Sprachliche Glättung eines rohen Caption-Blobs — Satzzeichen setzen, Absätze strukturieren, Minuten-Marker verteilen. KEINE Eigennamen-Korrektur, KEINE Faktenprüfung, KEINE Füllwort-Entfernung.

## Input

Worker 1 bekommt den **rohen Caption-Blob** — eine durch Leerzeichen verbundene Aneinanderreihung aller YouTube-Caption-Snippets, ohne Segmente, ohne Timestamps, ohne Formatierung.

| Eigenschaft | Typischer Wert |
|-------------|----------------|
| Format | Single line (keine Zeilenumbrüche) |
| Länge | ~30-55 KB Text |
| Wörter | ~4.000–10.000 (je nach Video-Länge) |
| Sprache | Deutsch (oder Zielsprache des Caption-Tracks) |

**Input-Datei:** `/tmp/yt_polish_input.txt` (vom Pipeline-Starter bereitgestellt)

## Aufgaben (streng, nichts anderes)

1. **Satzzeichen setzen**: Punkte, Kommas, Fragezeichen, Semikolons — wo sie fehlen. Achte besonders auf:
   - Fehlende Punkte am Satzende vor neuem Satzanfang
   - Fehlende Kommas bei Nebensätzen („Wenn X, dann Y")
   - Fehlende Fragezeichen bei Fragen
   - Tiefgestellte Punkte in Abkürzungen (`z.B.` statt `zB`)

2. **Absätze strukturieren**: Sinnvolle Absätze alle 2–4 Sätze — aber nur an logischen Sprechpausen/Themenwechseln, nicht erzwungen. Ein neuer Gedanke/Topic Shift = neuer Absatz.

3. **Sprachstil bewahren**: Umgangssprache bleibt — „halt", „quasi", „ähm", „echt", „so'n Zeug" gehören zum authentischen Ton. NICHT glattbügeln.

4. **Minuten-Marker setzen**: `## [MM:SS]`-Marker nach der Verteilungsmethodik (siehe unten). Der Marker muss VOR dem ersten Satz des Segments stehen.

### VERBOTEN

| ❌ Nicht machen | Weil |
|----------------|------|
| Inhaltliche Änderungen | Gehört zu keinem Worker — Caption bleibt wörtlich |
| Zusammenfassung / Kürzung | Der Merger erwartet 1:1-Länge |
| Eigennamen-Korrektur | Macht Worker 2 (Stil) — würde doppelt laufen |
| Faktenchecks | Macht Worker 3 — Worker 1 hat keinen Description-Kontext |
| Füllwort-Entfernung | „halt", „quasi", „ähm" sind Teil des authentischen Sprechstils |
| Vor-/Nachgeplauder | Output muss pur sein — nur der polierte Text |
| Umformulierungen | Auch wenn die Grammatik holpert — Caption-Charakter erhalten |

**Faustregel:** Wenn unsicher bei einer Phrase → im Original belassen. Worker 1 ist konservativ.

## Single-Line-Transkripte erkennen

YouTube-Auto-Captions kommen oft als **eine einzige Zeile** ohne Zeilenumbrüche — das ist der häufigste Input-Fall.

**Erkennung:**
- `wc -l /tmp/yt_polish_input.txt` zeigt `1` → Single-Line-File
- `read_file` zeigt `1|...` mit dem Textanfang in Zeile 1
- Der gesamte 30–55 KB Text liegt in einer Zeile

**Konsequenzen für die Verarbeitung:**
- `read_file` kann den ganzen Text laden (der `truncated`-Hinweis ist eine read_file-Viewport-Beschränkung, kein Datenverlust)
- Trotzdem lieber `python3 -c "with open(...) as f: print(len(f.read()))"` für die echte Länge
- `grep -oP` funktioniert trotz Single-Line — Regex matched über die gesamte Zeile
- Die Wortzahl über `python3 -c "text = open(...).read(); print(len(text.split()))"` ermitteln, nicht über `wc -w`

## Minuten-Marker-Verteilung

Wenn der Input-Caption-Blob **keine Timestamps** hat (häufigster Fall bei Auto-Captions), muss Worker 1 die Marker selbst setzen. Vorgehen:

### Schritt 0: Deutsche Abkürzungen schützen (vor dem Splitten!)

**Das ist der wichtigste Preprocessing-Schritt.** Deutschsprachige Transkripte enthalten Abkürzungen mit Punkt (`z.B.`, `d.h.`, `bzw.`), die von `.` + Space + Großbuchstabe-Heuristiken fälschlich als Satzenden erkannt werden.

**Schütze ALLE bekannten Abkürzungen vor dem Split:**

```python
protected = [
    ('z.B.', '§ZBE§'),
    ('d.h.', '§DHE§'),
    ('bzw.', '§BZW§'),
    ('ggf.', '§GGF§'),
    ('usw.', '§USW§'),
    ('etc.', '§ETC§'),
    ('ca.', '§CA§'),
    ('Nr.', '§NR§'),
    ('Dr.', '§DR§'),
    ('Mr.', '§MR§'),
    ('Prof.', '§PROF§'),
    ('Mio.', '§MIO§'),
    ('bspw.', '§BSPW§'),
    ('uvm.', '§UVM§'),
]

for orig, placeholder in protected:
    text = text.replace(orig, placeholder)

# Nach dem Splitten wieder zurücksetzen:
for orig, placeholder in protected:
    text = text.replace(placeholder, orig)
```

**Welche Abkürzungen schützen:** Alle die (a) einen Punkt enthalten, (b) im deutschen Sprachraum üblich sind und (c) gefolgt von einem Großbuchstaben sein können. Das Platzhalter-Format (`§XXX§`) stellt sicher, dass kein Platzhalter versehentlich ein natürliches Wort bildet.

**Praxiserfahrung (7.374 Wörter Input, 2026-07-04):** Ohne diesen Schutz wird `z.B.` als Satzende interpretiert → der folgende Satz wird fälschlich abgetrennt. Mit Schutz bleiben alle 14+ Abkürzungsvarianten intakt.

### Schritt 1: Ziel-Anzahl Marker bestimmen

```
ziel_marker = video_dauer_in_minuten + 1
# Beispiel: 42 Minuten → Marker 00:00 bis 42:00 = 43 Marker
# Beispiel: 36 Minuten → Marker 00:00 bis 36:00 = 37 Marker
```

### Schritt 2: Wortzahl pro Segment schätzen

```
wörter_pro_segment = gesamt_wortzahl // ziel_marker + 1
# Beispiel: 8758 Wörter ÷ 43 Marker ≈ 204 Wörter pro Segment
# Beispiel: 7374 Wörter ÷ 37 Marker ≈ 199 Wörter pro Segment
```

## Alternativer Pfad: Stufe-0-Pre-Polished-Input

Wenn der Input **bereits von Stufe 0** (deterministischer Pre-Polish) aufbereitet wurde, hat er schon Satzzeichen und braucht den komplexen Boundary-Scan nicht. Stattdessen gilt ein **vereinfachter Pfad**:

### Wann dieser Pfad greift

| Signal | Bedeutung |
|--------|-----------|
| Input hat bereits ~50+ Satzenden pro 1000 Wörter | Stufe-0 hat Punkte gesetzt |
| `wc -l` zeigt 1 (Single-Line) ABER `text.count('.')` ist > 300 | Die Captions sind bereits satzweise getrennt — nur die Zeilenumbrüche fehlen |
| Sprechgeschwindigkeit ~210-220 WPM (9100 Wörter bei 42:30) | Typisch für deutsche YouTube-Tutorials |

### Schritt 3a: Sentence Split mit einfachem Regex

Statt der Abkürzungs-Schutz-Heuristik reicht ein Boundary-Regex, der **auch deutsche Kleinbuchstaben** als Satzanfang erlaubt (weil Captions oft lowercase weiterlaufen):

```python
import re

# Wichtig: [a-z] mit reinnehmen, nicht nur [A-Z]!
boundary_re = re.compile(r'(?<=[.!?])\s+(?=[A-ZÄÖÜa-zäöüß])')
sentences = boundary_re.split(text)

# Nachsplit: ~467 Sätze bei 9100 Wörtern (≈19,5 Wörter/Satz)
```

**Warum `a-z`?** Deutsche Auto-Captions starten nach einem Punkt oft ohne Großschreibung weiter („... Setup. und dann klonen wir..."). Ohne `a-z` werden solche Stellen nicht gesplittet → künstlich lange „Sätze".

**Output:** Eine Liste von Sätzen. Keine Abkürzungs-Placeholder nötig — die bestehenden Satzzeichen aus Stufe-0 sind bereits korrekt gesetzt und werden nicht verändert.

### Schritt 3b: Absatz-Gruppierung (Rotation Pattern)

Sätze in Absätze von 2-4 Sätzen gruppieren. Ein einfaches Rotationsmuster liefert gleichmäßige Absatzlängen:

```python
group_sizes = [3, 3, 2]  # Durchschnitt: 2,67 Sätze/Absatz
paragraphs = []
i = 0
ci = 0
while i < len(sentences):
    size = group_sizes[ci % len(group_sizes)]
    chunk = sentences[i:i+size]
    paragraphs.append(' '.join(chunk))
    i += size
    ci += 1

# 9100 Wörter / 467 Sätze → ~175 Absätze
```

**Alternativ:** Auch andere Rotationen sind möglich (3, 2 oder 4, 3, 3). Ziel ist ein Durchschnitt von 2,5-3 Sätzen pro Absatz — das ergibt natürliche Lesbarkeit und genug Absätze für Marker.

### Schritt 3c: Marker-Verteilung über Paragraph-Index (statt Wort-Index)

Wenn der Text bereits in Absätze gruppiert ist, können Marker **direkt auf Paragraph-Indizes** gemappt werden — deutlich einfacher als die Word-Index-Methode:

```python
total_paragraphs = len(paragraphs)
marker_count = min(43, total_paragraphs)

# Marker k (0..42) → Paragraph-Index round(k * (total_paras - 1) / 42)
para_index_to_marker = {}
for k in range(marker_count):
    target = round(k * (total_paragraphs - 1) / (marker_count - 1)) if marker_count > 1 else 0
    para_index_to_marker[target] = k

# Ausgabe bauen
for idx, para in enumerate(paragraphs):
    if idx in para_index_to_marker:
        k = para_index_to_marker[idx]
        print(f'## [{k:02d}:00]')
        print()
    print(para)
    print()
```

**Warum das funktioniert:** Bei ~175 Absätzen auf 43 Marker entfallen ~4 Absätze pro Marker. Die `round(k * (N-1) / 42)`-Formel verteilt die Marker perfekt proportional — Marker 0 → Paragraph 0, Marker 42 → Paragraph 174 (letzter). Alle 43 Marker sind garantiert einmalig und decken den gesamten Text ab.

**Praxisdaten (Session 2026-07-04, k2p6WprtzFI, 42:30, 9100 Wörter):**
- 467 Sätze → 175 Absätze (Pattern: 3,3,2 → 2,67 Sätze/Absatz)
- 43 Minuten-Marker (00:00 bis 42:00) distribuiert
- **Verifikation:** 9100 Wörter exakt → 9100 Wörter (= 0,0% Drift)
- **498 End-Punctuation exakt erhalten** (0 hinzugefügt, 0 entfernt)
- Marker via Paragraph-Index-Methode: alle 43 eindeutig, keine Lücken

### Schritt 3d: Satzgrenzen finden (Raw-Caption-Workflow)

**Dieser Pfad ist NUR für Input OHNE Stufe-0-Vorverarbeitung.** Wenn der Input bereits Satzzeichen hat → den alternativen Pfad oben (Schritt 3a–3c) verwenden.

Finde alle `.`, `?`, `!` gefolgt von Space + Großbuchstabe — das sind wahrscheinliche Satzenden:

```python
boundaries = []
for i in range(2, len(text) - 2):
    if text[i] == ' ' and text[i+1].isupper() and (text[i-1] in '.!?'):
        boundaries.append(i + 1)  # Position NACH dem Space
```

Die Anzahl der Boundaries gibt einen Hinweis auf die durchschnittliche Satzlänge. Typisch: ~370 Boundaries bei 7.374 Wörtern → ~20 Wörter pro Satz.

### Schritt 4: Segment-Grenzen an Satzenden ausrichten (Word-Index-Methode)

Nicht starr nach Wortzahl trennen! Stattdessen die **Word-Index-Methode** verwenden — das ist präziser als die Zeichen-Fenster-Heuristik:

**Phase 4a: Wort-Positionen-Tabelle bauen**

```python
words = text.split()
word_positions = []
pos = 0
for w in words:
    idx = text.find(w, pos)
    if idx >= 0:
        word_positions.append(idx)
        pos = idx + len(w)
```

**Phase 4b: Für jede Ziel-Minute den nächsten Satz split finden**

```python
chunks = []  # Schnittpunkte (Text-Positionen)
target_wpc = len(words) / ziel_marker  # Wörter pro Chunk

for chunk_idx in range(ziel_marker - 1):  # z.B. 36 Cuts für 37 Chunks
    target_word_idx = int((chunk_idx + 1) * target_wpc)
    target_text_pos = word_positions[target_word_idx]
    
    # Nächste Boundary >= target finden
    best = None
    for b in boundaries:
        if b >= target_text_pos:
            best = b
            break
    if best is None:
        best = word_positions[min(target_word_idx + 5, len(word_positions) - 1)]
    chunks.append(best)
```

**Phase 4c: Text in Chunks schneiden**

```python
prev = 0
for i, cut in enumerate(chunks + [len(text)]):  # + letztes Segment bis Ende
    print(f"## [{i:02d}:00]")
    print(text[prev:cut].strip())
    print()
    prev = cut
```

**Warum die Word-Index-Methode besser ist als die Fenster-Heuristik:**
1. **Präzise Wortzahl pro Segment**: `target_wpc` wird genau eingehalten (± wenige Wörter)
2. **Kein überlappendes Fenster nötig**: Die alte Fenster-Heuristik (`±200 Zeichen`) ist bei Single-Line-Texten unnötig komplex
3. **Letztes Segment korrekt behandelt**: `chunks + [len(text)]` stellt sicher, dass der Rest des Textes in das letzte Segment fällt
4. **Deterministisch**: Gleicher Input → gleiche Chunks, kein Raten

### Schritt 5: Absätze im Segment verteilen

Jedes Segment (≈1 Minute Video) sollte ~3-4 Absätze enthalten. Dazu den Text des Segments in etwa gleich große Absätze teilen:
- 2-4 Sätze pro Absatz
- Absätze an Satzenden trennen, nicht innerhalb eines Satzes
- Absätze durch **Leerzeile** trennen (nicht durch doppelten Zeilenumbruch)

**Hinweis:** In Stufe 1 (Worker 1 INHALT) reicht es, die Chunks mit `## [MM:00]` zu markieren und als einen Absatz pro Chunk zu belassen. Absätze innerhalb der Chunks sind optional — sie werden in Stufe 2 oder im Merger verfeinert.

**Ergebnisse aus der Praxis:**

| Video | Dauer | Wörter | Stufe-0-Punct | Marker | Wörter/Segment | Boundaries | Drift | End-Punct-Erhalt |
|-------|-------|--------|--------------|--------|----------------|------------|-------|-------------------|
| Obsidian+Claude Code (2026-07-04) | 36:24 | 7.374 | — | 37 (00:00–36:00) | 199 | 372 | <5% | — |
| Claude Code 8 Best Practices (2026-03-15) | 42:48 | 8.758 | — | 43 (00:00–42:00) | 204 | ~420 | <5% | — |
| KI-Betriebssystem (2026-07-04, k2p6WprtzFI) | 42:30 | 9.100 | 498 ✅ | 43 (00:00–42:00) | 212 | 467 | **0,0%** | **498→498 (100%)** |

## Self-Verification (zwingend nach dem Schreiben)

### 1. Marker-Anzahl prüfen

```bash
# Zählt ALLE Marker — wichtig: nicht auf [0 eingrenzen!
grep -c '^## \[' /tmp/yt_polish_output_inhalt.md
# Muss EXAKT der Ziel-Anzahl entsprechen (z.B. 43)
```

⚠️ **Bekannte Falle:**  
`grep -c "^## [0"` zählt NUR Marker von 00:00 bis 09:xx — Marker ab Minute 10 werden übersehen.  
**Richtig:** `grep -c '^## \['`

### 2. Letzten Marker prüfen

```bash
grep -E '^## \[' /tmp/yt_polish_output_inhalt.md | tail -1
# Muss ## [MM:SS] sein, wobei MM = video_dauer_in_minuten (z.B. ## [00:42])
```

### 3. Wortzahl prüfen

```bash
wc -w /tmp/yt_polish_output_inhalt.md
```

**Erwartung:** Drift < 5% gegenüber Input-Wortzahl.

**Praxishinweis:** `wc -w` zählt ALLE Tokens — inklusive Marker-Text („00", „02" etc.). Marker-Text ist ~1,5-2% der Token-Anzahl. Wenn Input = 8758 Wörter und Output = 8844 ist das OK (davon ~86 Wörter = Marker-Text).  
**Bag-of-Words-Vergleich** (nur Inhalt) sollte 0 Differenz zeigen.

### 4. End-Punctuation-Preservation-Check (neu in v1.2)

**Wichtigster Qualitätsindikator für Stufe-0-Input:** Der Output muss exakt so viele Satzzeichen enthalten wie der Input — weder mehr noch weniger.

```bash
# Input
python3 -c "import sys; t=open(sys.argv[1]).read(); print(t.count('.')+t.count('!')+t.count('?'))" /tmp/yt_polish_input.txt

# Output (Marker-Syntax rausgerechnet)
python3 -c "
import sys, re
t=re.sub(r'^## \[\d+:\d+\]', '', open(sys.argv[1]).read(), flags=re.MULTILINE)
print(t.count('.')+t.count('!')+t.count('?'))
" /tmp/yt_polish_output_inhalt.md
```

**Erwartung:** Input-Wert === Output-Wert.  
Wenn der Input 498 End-Punctuation-Symbole hat, muss der Output ebenfalls exakt 498 haben.  
Abweichungen bedeuten: (a) ein Satzzeichen wurde versehentlich gelöscht oder (b) der Split-Algorithmus hat ein Satzende doppelt/schlecht behandelt.

**Praxisergebnis (k2p6WprtzFI, 9100 Wörter):** 498 → 498 (0,0% Abweichung). Der einfache Boundary-Regex auf dem Stufe-0-Input produziert garantiert keinen Punctuation-Drift.

### 5. Bag-of-Words-Verifikation (optional)

```python
import re
from collections import Counter

def normalize(t):
    t = re.sub(r'## \[\d\d:\d\d\]', '', t)  # Marker entfernen
    t = re.sub(r'===START_INHALT===|===END_INHALT===', '', t)
    t = re.sub(r'[^\w\s]', '', t)   # Satzzeichen entfernen
    t = re.sub(r'\s+', ' ', t).strip().lower()
    return t

raw_bag = sorted(normalize(input_text).split())
out_bag = sorted(normalize(output_text).split())

raw_count = Counter(raw_bag)
out_count = Counter(out_bag)

for w in raw_count:
    diff = raw_count[w] - out_count[w]
    if diff != 0:
        print(f'{w}: fehlt {diff}' if diff > 0 else f'{w}: zu viel {-diff}')
```

## Output-Wrapper-Format

Datei: `/tmp/yt_polish_output_inhalt.md`

```text
===START_INHALT===
## [00:00]

<Paragraph 1 zu diesem Segment>

<Paragraph 2 zu diesem Segment>

## [00:01]

...
===END_INHALT===
```

Die Marker `===START_INHALT===` / `===END_INHALT===` sind zwingend — der Merger parst sie, um Worker-1/2/3-Output zu unterscheiden.

## Stdout-Summary nach Fertigstellung

Nach dem Schreiben auf stdout ausgeben (nicht in die Datei schreiben):

```text
- ANZAHL_WOERTER: <Zahl>
- MINUTEN_MARKER: <Anzahl>
- AENDERUNGEN: <kurze Liste der durchgeführten Glättungen>
```

Beispiel aus der Praxis:
```
- ANZAHL_WOERTER: 8758
- MINUTEN_MARKER: 43
- AENDERUNGEN: Satzzeichen ergänzt, 173 Absätze strukturiert, Minuten-Marker 00:00–00:42 gesetzt
```

## Bekannte Pitfalls (aus der Praxis)

### ⚠️ Zu viele Marker gesetzt

Statt 43 (00:00 bis 42:00) werden manchmal 44+ gesetzt (00:00 bis 43:00+).  
**Ursache:** Der Split-Algorithmus erzeugt ein zusätzliches Segment am Ende, wenn die letzte Split-Position < total_chars liegt.  
**Fix:** Immer den letzten Marker mit `grep -E '^## \[' | tail -1` prüfen. Die MAX-Minute muss `video_dauer_in_minuten` sein (im Beispiel: 42).

### ⚠️ „Belassen im Original" vs. „Marker setzen" Konflikt

Die Spec sagt: „Wenn unsicher, im Original belassen." Aber das Output-Format verlangt explizit `## [MM:SS]`-Marker.  
**Regel:** Bei Input-ohne-Marker ist MARKER-SETZEN die richtige Entscheidung. Die Output-Spec überstimmt die „belassen"-Regel. Ein Output ohne Marker ist für den Merger unbrauchbar.

### ⚠️ Wortzahl-Drift durch Marker-Text

`wc -w` zählt Marker wie `## [00:15]` als 3 Wörter. Bei 43 Markern sind das ~86 zusätzliche Wörter (~1% Drift).  
Kein Bug — aber bei der Verifikation muss man wissen, dass `wc -w` das Output gegenüber dem Input um ~1-2% aufbläht.

### ⚠️ Sentence-Split heuristics bei Fragen/Ausrufen

`?` und `!` sind seltener als `.` — aber genauso gültige Satzenden. Der Split-Algorithmus muss alle drei berücksichtigen, sonst entstehen unnatürlich lange Segmente nach Fragezeichen.

### ⚠️ Letztes Segment kann kürzer sein

Das letzte Segment (z. B. 00:42) ist oft kürzer als die anderen — weil das Transkript vor der vollen Minute endet. Das ist normal und kein Fehler. Solange der `===END_INHALT===-Marker danach kommt, ist alles korrekt.

### ⚠️ Single-Line-Transkript: read_file zeigt nur erste Zeile an

`read_file` liest bei Single-Line-Dateien den gesamten Text (versteckt hinter `1|...`). Der `truncated`-Hinweis kann irreführen.  
**Fix:** Immer `python3 -c "len(open(...).read())"` für die echte Größe, nie `read_file`-Ansicht allein als Größen-Indikator nutzen.

### ⚠️ `words = text.split()` lässt Marker intakt

Die `word_positions`-Tabelle wird mit dem **geschützten** Text (Abkürzungen als Placeholder) gebaut. Nach dem Restore der Placeholder stimmen die Positionen trotzdem, weil Placeholder und Original dieselbe Länge haben.

### ⚠️ Abkürzungs-Schutz muss VOR dem Boundaries-Scan kommen

Die Abkürzungs-Placeholder (Schritt 0) müssen gesetzt sein, **bevor** Schritt 3 die Satzgrenzen scannt. Sonst erzeugen `z.B.`, `d.h.` etc. false-positive Boundaries.

## Variante: Input mit vorgegebenen Minuten-Markern (Stufe-0-Variante)

**Wann dieser Pfad greift:** Wenn der Input **bereits `## [MM:00]`-Marker enthält** und der Königin-Worker die Marker-Verteilung dem Worker 1 abgenommen hat (z.B. weil ein vorgeschalteter Stufe-0-Deterministic-Pass oder ein anderer Worker die Marker schon gesetzt hat). In diesem Fall ist Worker 1 ein **reiner Inhalts-Polisher** ohne Marker-Verteilungs-Logik.

**Beispiel-Setup (Session 2026-07-09, Julian Remote-Control-Video, pvhphecd70Y, 22:57):**
- Input: `/tmp/yt_remote_workers/input_transcript.md` (4906 Wörter, 23 Marker `## [00:00]` … `## [22:00]` EXAKT vorgegeben)
- Output: `/tmp/yt_remote_workers/output_worker1_inhalt.md`
- Wrapper-Format (vom Königin vorgegeben):
  ```text
  ===START_WORKER1_INHALT===
  ## [00:00]
  <polierter Text mit Absatz-Brüchen INNERHALB der Marker>
  ## [01:00]
  ...
  ===END_WORKER1_INHALT===
  ===STATUS_WORKER1_INHALT===
  Woerter: 4964
  Gefixt: Begriff_A -> Begriff_B (Nx), ...
  Absaetze: 69 (von 23 Eingangs-MonoBlocks, je 2-4 Absaetze pro Block)
  Minuten-Marker: 23/23 erhalten
  Wort-Drift: +1.18% (innerhalb +-5% Limit)
  BEWUSST_NICHT_GEFIXT: Cloud (Claude), T-Max (tmux), Claud/Clot/Clud/Clode,
    SLRemote Control, SlashG, SLGal, SLclear, Resent, Rustinger, conhost, KFM2,
    crystalflow, Routines, Cowork, [musik], Front-E Design Skill
  ===END_STATUS_WORKER1_INHALT===
  ```

### Pflicht-Aufgaben (bei vorgegebenen Markern)

1. **Satzzeichen setzen** — wie oben (Punkte, Kommas, Fragezeichen am Satzende)
2. **Absätze strukturieren** INNERHALB jedes Marker-Blocks (alle 2-4 Sätze neuer Absatz) — NICHT zwischen Markern
3. **Auto-Caption-Hörfehler im Sprachfluss fixen** (siehe unten: Was ist erlaubt, was nicht)
4. **Minuten-Marker UNVERÄNDERT lassen** — keiner umbenennen, keinen verschieben, keinen hinzufügen
5. **Satz-Reihenfolge NICHT ändern** — nur Interpunktion und Absatz-Brüche

### VERBOTEN (bei vorgegebenen Markern — strikter als bei Marker-Erstellung)

| ❌ Nicht machen | Warum besonders wichtig bei vorgegebenen Markern |
|----------------|---------------------------------------------------|
| **Eigennamen korrigieren** | Gehört zu Worker 2 — siehe unten „Eigennamen-Contract" |
| Marker verschieben/löschen | Königin hat die Marker-Verteilung bewusst gewählt |
| Wörter umstellen | Caption-Charakter zerstören |
| Stille „Verbesserungen" (Glätten von „halt", „quasi") | Authentischer Sprachstil geht verloren |
| Zusammenfassen/Kürzen | Drift-Budget wird gesprengt |

### Auto-Caption-Hörfehler: Scope-Regel (neu in v1.3, Session 2026-07-09)

**Faustregel:** Wenn der Fix **keinen Eigennamen** berührt, ist er erlaubt. Wenn er **einen Eigennamen** berührt, ist er Worker 2's Job.

| Hörfehler-Typ | Beispiel | Worker 1 erlaubt? |
|--------------|----------|-------------------|
| **Deutsche-Wort-Typo** | `Anmoldeformular` → `Anmeldeformular` | ✅ Ja |
| **Deutsche-Wort-Typo** | `DDatei` → `Datei` | ✅ Ja |
| **Deutsche-Wort-Typo** | `erknüpfen` → `verknüpfen` | ✅ Ja |
| **Deutsche-Wort-Typo** | `züllen` → `füllen` | ✅ Ja |
| **Deutsche-Wort-Typo** | `Modis` → `Modi` | ✅ Ja |
| **Grammatik-/Interpunktion** | `keiner Fehler` → `keine Fehler` | ✅ Ja |
| **Grammatik-/Interpunktion** | `Das heiß,` → `Das heißt,` | ✅ Ja |
| **Großschreibung** | `ca. Eine` → `ca. eine` (Satzmitte) | ✅ Ja |
| **Zahl-Compound** | `10 mal` → `10-mal` | ✅ Ja (wenn vorhanden) |
| **Eigennamen-Hörfehler** | `Cloud` → `Claude` | ❌ Nein → Worker 2 |
| **Eigennamen-Hörfehler** | `Tmax`/`T-Max` → `tmux` | ❌ Nein → Worker 2 |
| **Eigennamen-Hörfehler** | `Hostinger`/`Rustinger`/`conhost` | ❌ Nein → Worker 2 |
| **Eigennamen-Hörfehler** | `SLRemote Control`/`slem Control` → `/remote-control` | ❌ Nein → Worker 2 |
| **Eigennamen-Hörfehler** | `Resent` → `Resend` (Service-Name) | ❌ Nein → Worker 2 |
| **Eigennamen-Hörfehler** | `Clot`/`Claud`/`Clud`/`Clode` → `Claude` | ❌ Nein → Worker 2 |
| **Eigennamen-Hörfehler** | `SlashG`/`SLGal`/`SLclear` → `/goal`/`/clear` | ❌ Nein → Worker 2 |

**Kurzformel:** „Wenn der Fix kein deutsches Wort produziert, ist er Worker 1's Job." Eigennamen-Hörfehler produzieren IMMER einen anderen Eigennamen.

### Eigennamen-Contract: wie man „nicht mein Job" kommuniziert

**Im Status-Block am Dateiende dokumentieren welche Hörfehler man BEWUSST stehen gelassen hat.** Das macht die Eigennamen-Übergabe an Worker 2 explizit, statt zu raten was noch zu tun ist.

**Best Practice:** Diese `BEWUSST_NICHT_GEFIXT`-Liste im **STATUS-Block** referenziert die Königin's Eigennamen-Liste (meist in `context.md` der Königin-Briefings dokumentiert). Worker 2 liest das STAGE-OUTPUT aus dem Status-Block und weiß genau, was noch zu tun ist.

### Briefing-Widersprüche: Beispiel vs. Verboten-Liste (Pitfall aus Session 2026-07-09)

**Symptom:** Das Königin-Briefing enthält **beides**:
- Im Aufgaben-Block: „Repariere Wortbrüche wie 'Cloud Code -Skill' → 'Claude-Code-Skill'"
- Im Verboten-Block: „KEINE Eigennamen-Korrekturen — wenn du 'Cloud Code' siehst, lass es stehen!"

**Welcher Block gewinnt?** Im Zweifel der **VERBOTEN-Block**, weil:
1. Eigennamen-Fixes sind destruktiv (sie verändern den Identifier, den andere Worker erwarten)
2. Wortbruch-Reparaturen sind additiv (sie verändern das Wort selbst, nicht den Identifier)
3. Königin-Briefings schreiben Verbote meist nach den Erlaubnissen — Verbote sind die spätere, korrigierte Spec

**Faustregel:** Wenn ein Briefing-Beispiel sagt „repariere X" und der Verbote-Block sagt „lasse X stehen", dann ist das Beispiel oft als **Generalisierung gemeint** (Compound-Wortbrüche, deutsche Wörter) — der Verbote-Block nennt den **konkreten Sonderfall** (Eigennamen). Beide gelten: repariere deutsche Compound-Wortbrüche, aber NICHT Eigennamen.

**Verifikation:** Wenn unsicher → **im Original belassen**. Worker 1 ist konservativ. Worker 2 hat die Königin's Eigennamen-Liste und kann den Begriff später sauber fixen.

### Drift-Budget bei vorgegebenen Markern

| Aspekt | Marker-selbst-erstellen | Marker-vorgegeben |
|--------|------------------------|-------------------|
| `wc -w` Overhead | +1-2% durch Marker-Text (`## [00:15]` als 3 Tokens) | **0%** (Marker kommen rein, gehen raus, kein Drift) |
| Drift-Allowed | +5% (Großzügig wegen Marker-Inflation) | +1.5% realistisch — nur Interpunktion + Absatz-Brüche |
| Echte Inhalts-Drift | 0% (gleiche Wörter) | 0% (gleiche Wörter) |
| End-Punctuation-Erhalt | muss == Input sein | darf zunehmen (Punkte ergänzen erlaubt) |

**Wichtig:** Bei vorgegebenen Markern ist das Drift-Budget **enger**, weil Marker-Inflation wegfällt. Jeder zusätzliche Punkt/Komma zählt 1:1 in `wc -w`. Faustregel: nicht mehr als 1 neues Satzzeichen pro 50 Wörter setzen (sehr konservativ).

**Praxisergebnis (Session 2026-07-09):**
- 4906 → 4964 = +58 Wörter = +1.18% Drift
- Davon ~49 echte Wörter-Unterschiede (9 Wort-Fixes, je 1-3 Zeichen Unterschied)
- Rest = Interpunktions-Ergänzungen (Punkte am Satzende)

### grep-Substring-Match-Falle (Pitfall aus Self-Verification)

**Symptom:** Man will prüfen ob ein Hörfehler gefixt wurde, z.B. `erknüpfen → verknüpfen`. Dann:
```bash
grep -c "erknüpfen" output.md  # Gibt 1 zurück, obwohl "erknüpfen" gar nicht im Text steht
```

**Ursache:** `verknüpfen` enthält `erknüpfen` als Substring (Position 1). `grep -c` zählt jede Zeile die den Pattern MATCHT — und „verknüpfen" matched per Substring-Containment.

**Korrekte Verifikation mit Word-Boundary:**
```bash
grep -cE "(^|[^a-zäöüß])erknüpfen([^a-zäöüß]|$)" output.md  # → 0 (richtig)
```

Oder mit Python (empfohlen):
```python
import re
text = open("output.md").read()
matches = re.findall(r"\berknüpfen\b", text)
print(f"Standalone 'erknüpfen': {len(matches)}")  # → 0
matches = re.findall(r"\bverknüpfen\b", text)
print(f"Standalone 'verknüpfen': {len(matches)}")  # → 1
```

**Lesson:** Bei Self-Verification immer Word-Boundary-Regex (`\b`, `re.findall`, oder Python `in`-Operator auf `word_tokenize`) statt naivem `grep -c`. Sonst bekommt man False-Positives bei ähnlichen Strings.

### Output-Wrapper bei vorgegebenen Markern

Der Königin-vorgegebene Wrapper ist **anders** als der Standard-Stufe-3-Wrapper:

```text
===START_WORKER1_INHALT===
## [00:00]

<Absatz 1>

<Absatz 2>

## [01:00]

<Absatz 3>
...
===END_WORKER1_INHALT===
===STATUS_WORKER1_INHALT===
Woerter: <Zahl>
Gefixt: Begriff_A -> Begriff_B (Nx), Begriff_C -> Begriff_D (Mx)
Absaetze: <Anzahl> (von <Anzahl> Eingangs-MonoBlocks)
Minuten-Marker: <Erhalten>/<Total> erhalten
Wort-Drift: +/-X% (innerhalb +-5% Limit)
BEWUSST_NICHT_GEFIXT: <Liste der Hörfehler die Worker 2 macht>
===END_STATUS_WORKER1_INHALT===
```

**Unterschied zum Standard-Stufe-3-Wrapper:**
- `===START_WORKER1_INHALT===` statt `===START_INHALT===` (Königin's Naming-Convention)
- `BEWUSST_NICHT_GEFIXT`-Sektion im Status (siehe oben)
- `Minuten-Marker: N/Total erhalten` (kein „gesetzt", weil schon vorgegeben)
- `Absaetze:` mit Vergleich zur Eingangs-MonoBlock-Anzahl (zeigt wie stark strukturiert wurde)

## Vergleich mit Worker 2 und Worker 3

| Aspekt | Worker 1 (Inhalt) | Worker 2 (Stil) | Worker 3 (Faktencheck) |
|--------|-------------------|-----------------|------------------------|
| Ändert Text | ✅ Ja | ✅ Ja | ❌ Nein (nur Report) |
| Satzzeichen | ✅ Ja | ❌ Nein | ❌ Nein |
| Absätze | ✅ Ja (auch wenn Marker vorgegeben) | ❌ Nein | ❌ Nein |
| Minuten-Marker | ✅ Ja (nur wenn nicht vorgegeben) | ❌ Nein | ❌ Nein |
| Auto-Caption-Wort-Typos | ✅ Ja (siehe Scope-Regel oben) | ❌ Nein | ❌ Nur melden |
| Eigennamen | ❌ Nein (siehe Contract oben) | ✅ Ja | ❌ Nur melden |
| Fakten | ❌ Nein | ❌ Nein | ✅ Ja |
| Input | Roh-Blob (oder Stufe-0-Pre-Polished mit/ohne Marker) | Roh-Blob + Description | Roh-Blob + Description |
| Output | `/tmp/yt_polish_output_inhalt.md` | `/tmp/yt_polish_output_stil.md` | `/tmp/yt_polish_output_faktencheck.md` |

## Siehe auch

- `youtube-transcript-saver/SKILL.md` — Stufe-3-Pipeline-Übersicht und Merger-Pitfalls
- `references/worker2-stil-methodology.md` — Worker-2-Methodik (Eigennamen-Korrektur, läuft parallel)
- `references/faktencheck-methodology.md` — Worker-3-Methodik (Faktencheck, läuft parallel)
- `references/known-hearing-errors.md` — Such-Matrix für Post-Merger-Verifikation

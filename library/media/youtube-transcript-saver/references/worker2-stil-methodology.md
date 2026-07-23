# Worker-2-Methodik: Stil + Eigennamenkorrektur

## Wann einsetzen

Worker 2 (Stil + Eigennamen) ist der zweite parallele Worker in **Stufe 3** der Caption-Polishing-Pipeline.
Er läuft **parallel** zu Worker 1 (Inhalt/Sprache) und Worker 3 (Faktencheck) und wird erst nach Fertigstellung aller drei Worker durch den Merger zusammengeführt.

**Seine Aufgabe:** Auto-Caption-Hörfehler bei **Eigennamen, Tool-Namen, Modell-Namen und Fachbegriffen** korrigieren. Der Worker ändert NUR Namen und Fachtermini — keine Satzzeichen, keine Absatz-Struktur, keine Grammatik, keine Füllwörter.

## Inputs

Worker 2 bekommt — je nach Pipeline-Variante — bis zu DREI Eingabedateien:

| Datei | Inhalt | Variante |
|-------|--------|----------|
| `/tmp/yt_remote_workers/input_transcript.md` | **Stufe-0-poliertes** Transkript (Minuten-Marker erhalten, Wortbrüche geglättet, **aber Eigennamen z.T. noch verhunzt**) | Swarm-Variante (Stufe 3, Multi-Worker) |
| `/tmp/yt_remote_workers/context.md` | **Heuristik-Liste** für genau dieses Video (vom Orchestrator/Planner bereitgestellt, enthält Channel, Tools, erwartete Hörfehler-Patterns) | Swarm-Variante |
| `/tmp/yt_remote_workers/input_raw_caption.txt` | Original-Auto-Caption (für Cross-Check wenn unsicher, was Julian wirklich gesagt hat) | Swarm-Variante, optional |
| `/tmp/yt_polish_input.txt` | Roh-Transkript (eine Zeile, ~30 KB, keine Formatierung) | Stufe-2/3-Standard |
| `/tmp/yt_polish_description.txt` | YouTube-Description (Titel, Channel, Upload-Dauer, Views, Beschreibung, Lernziele, Links, Zeitstempel, Tags) | Stufe-2/3-Standard |

**⚠️ Swarm-Variante (Stufe 3 Multi-Worker) — entscheidender Unterschied:**

In der Swarm-Variante bekommt Worker 2 **NICHT die Description** zum Scannen, sondern eine **vorbereitete `context.md`** mit der expliziten Heuristik-Liste für DIESES Video. Das hat zwei Konsequenzen:

1. **Disziplin:** Der Worker DARF die Liste NICHT erweitern oder raten. Wenn ein Begriff nicht in der Heuristik-Liste steht und nicht eindeutig im Kontext erkennbar ist → `UNSICHER` dokumentieren, Original belassen.
2. **Kürzere Vorbereitung:** Kein Description-Scan nötig — die Liste kommt fertig. Worker kann sofort mit Pass 3 (Regex-Anwendung) loslegen.

**Vergleich beider Varianten:**

| Aspekt | Standard (Stufe 2/3, Description-Scan) | Swarm (Stufe 3 Multi-Worker, context.md) |
|--------|---------------------------------------|------------------------------------------|
| Kontext-Quelle | Description selbst scannen | Vorbereitete Heuristik-Liste |
| Begriffs-Liste | Self-extracted aus Tags/Lernzielen | Fest vorgegeben vom Planner |
| Erweiterung erlaubt | Ja (Description gibt Hinweise) | Nein (strenge Disziplin) |
| Output-Format | `===START_STIL===` Marker | `===START_WORKER2_STIL===` Marker + Status-Block am Dateiende |
| Status-Pflicht | Optional | **Zwingend** (Aggregator parsed Counts) |

## Workflow

### 1. Alle Inputs lesen

**Standard-Variante:**
```python
with open('/tmp/yt_polish_input.txt', 'r') as f:
    text = f.read()

with open('/tmp/yt_polish_description.txt', 'r') as f:
    desc = f.read()
```

**Swarm-Variante:**
```python
with open('/tmp/yt_remote_workers/input_transcript.md', 'r') as f:
    text = f.read()  # Stufe-0-poliert, Minuten-Marker erhalten

with open('/tmp/yt_remote_workers/context.md', 'r') as f:
    context = f.read()  # Heuristik-Liste für DIESES Video

# Optional für Cross-Check bei Unsicherheit:
with open('/tmp/yt_remote_workers/input_raw_caption.txt', 'r') as f:
    raw_caption = f.read()  # Was Julian WIRKLICH gesagt hat
```

⚠️ **Single-Line-Transkripte:** YouTube-Auto-Captions kommen oft als ein einziger langer Text (keine Zeilenumbrüche). `read_file` zeigt dann `1|...`. Das ist normal — Python kann den Text trotzdem vollständig lesen.

⚠️ **Stufe-0-Output ist bereits teilweise korrigiert:** Im Swarm-Setup hat Worker 1 (Stufe 0) **bereits** einige Hörfehler deterministisch vorab gefixt. Das bedeutet: Patterns wie `Tmax → tmux` können teilweise schon korrekt sein — die Heuristik-Liste muss trotzdem gegen den vollen Bestand geprüft werden, da Worker 1 nicht alle Varianten abdeckt. Beispiel aus Session 2026-07-09 (pvhphecd70Y): Worker 1 hatte `Tmax` in 8 von 9 Fällen gefixt, aber `T-Max quasi ein Terminal im Terminal` (mit Bindestrich) war übersehen worden.

### 2. Heuristik-Liste aus context.md extrahieren (Swarm-Variante)

In der Swarm-Variante ist die Liste explizit vorgegeben. Format-Beispiel aus `context.md`:

```markdown
BEKANNTE HOERFEHLER-PATTERNS FUER DIESES VIDEO:
- "Tmax"/"TMAX" -> tmux (8x im Roh-Blob)
- "SLGal" -> /goal
- "SlashLOP" / "Slashloop" -> /loop
- "SLclear" -> /clear
- "Slash Goal" / "Slash Loop" -> /goal / /loop
- "Cloud" / "Cloud Code" (Standalone) -> Claude / Claude Code
- "Hermis" -> Hermes
- "Gitub" -> GitHub
- "Anthopic" -> Anthropic
```

**Methode:** Jede Zeile der Form `-"<pattern>" -> <ersatz>` wird zu einem Regex-Pattern. Bei mehreren Alternativen (`"SlashLOP" / "Slashloop"`) wird jede einzeln aufgenommen.

**Standard-Variante (Description-Scan):**

Extrahiere aus der Description: Channel-Name, Tools, Modelle, Plattformen, Tags, die im Transkript vorkommen könnten.

**Beispiele aus der Praxis:**
- Tags: `Obsidian, Claude Code, Claude Cowork, Second Brain` — viele werden im Transkript erwähnt
- Modell-Namen: `Claude Opus, Claude Sonnet` — in Captions oft verhunzt
- Plugin-Namen: `Excalidraw, BRAT` — können als "Excaly Drawrop", "Brad" verhunzt sein

### 3. Regex-basierte Korrekturen (deterministisch, kein LLM)

**Prinzip:** Längste Patterns zuerst, kürzeste zuletzt. So werden Substring-Matches vor längeren Patterns vermieden.

#### Aufbau einer Fix-Routine

```python
import re

text = original_text
fixes = {}

def fix(pattern, repl, key):
    """Ersetzt global und zählt Treffer."""
    global text
    new_text, n = re.subn(pattern, repl, text)
    text = new_text
    fixes[key] = n
```

**Reihenfolge ist entscheidend — 4 Prioritätsstufen**

```python
# STUFE 1: Längste Compound-Patterns zuerst (mehrere Wörter, ggf. mit Sonderzeichen)
fix(r'\bCloud\s+Cowork\b',     'Claude Cowork',       'Cloud Cowork→Claude Cowork')
fix(r'\bExcalid\s+Drop\b',     'Excalidraw Plugin',   'Excalid Drop→Excalidraw Plugin')

# STUFE 2: Patterns mit Space (mehrere Wörter ohne Zusammenschreibung)
fix(r'\bCloud\s+Code\b',       'Claude Code',         'Cloud Code→Claude Code')
fix(r'\bClaud\s+Cowork\b',     'Claude Cowork',       'Claud Cowork→Claude Cowork')

# STUFE 3: Patterns ohne Space (ein Wort, vollständig oder teilweise amputiert)
fix(r'\bCludt\b',              'Claude',              'Cludt→Claude')
fix(r'\bClot\b',               'Claude',              'Clot→Claude')
fix(r'\bExcalidrawrop\b',      'Excalidraw',          'Excalidrawrop→Excalidraw')

# STUFE 4: Kürzeste Einzelwort-Ersetzungen und konsistente Kleinschreibungen
fix(r'\bclaw\b',               'Claw',                'claw→Claw (Großschreibung)')
```

**Warum 4 Stufen statt nur "lange vor kurz"?** Compound-Patterns mit unterschiedlicher Wortanzahl (Stufe 1: 3 Wörter, Stufe 2: 2 Wörter) brauchen eigene Prioritätsebenen, damit z. B. `"Cloud Cowork"` nicht durch `"Cloud" → "Claude"` zerstört wird bevor `"Cloud Cowork" → "Claude Cowork"` greifen kann.

### ⚠️ Pass-Ordering-Falle: Compound-Formen ZUERST, dann Standalone

**Kritischer Pitfall (Session 2026-07-09, Worker 2 / pvhphecd70Y):** Wenn dein Standalone-Pattern `Claud` → `Claude` ist und du es mit negativem Lookahead `(?!\s*Code\b)` absicherst (damit `Claude Code` nicht doppelt gepatched wird), und du gleichzeitig Compound-Formen wie `Cloud Desktop App` → `Claude Desktop App` VOR diesem Pattern ausführst — dann matcht der Standalone-Pattern auf das bereits korrigierte `Claude` und produziert `Claudee Desktop App`.

**Konkretes Bug-Beispiel:**

```python
# FALSCHE Reihenfolge (erzeugt "Claudee"):
fix(r'\bCloud Desktop App\b', 'Claude Desktop App')   # Stufe A
fix(r'\bClaud(?! Code)\b',    'Claude')                # matcht jetzt AUCH das "Claud" in "Claude Desktop App"

# RICHTIGE Reihenfolge (kein Bug):
fix(r'\bClaud(?! Code)\b',    'Claude')                # Standalone zuerst — matcht "Claud" in "Hey Claud, ..."
fix(r'\bCloud Desktop App\b', 'Claude Desktop App')   # Compound danach — unabhängig
```

**Saubere Variante (Lookahead-Ordering unabhängig):** Statt mit Lookahead zu jonglieren, einfach **Standalone-Patterns IMMER vor Compound-Patterns** ausführen. Dann ist `Claud(?! Code)` gar nicht mehr nötig — `Claude Code` wurde von Worker 1 (Stufe 0) bereits korrekt geliefert und die Standalone-Patterns matchen es nicht (weil `Claud` nicht in `Claude` enthalten ist).

**Generalisierung — die Regel lautet:**

| Pass | Was wann |
|------|---------|
| **1. Slash-Commands** (längste zuerst) | `SLRemote Control` → `/remote Control` bevor `/loop` alleine verarbeitet wird |
| **2. Eigennamen-Repairs** (nicht-Cloud) | `T-Max` → `tmux`, `Rustinger` → `Hostinger` |
| **3. Auto-Caption-Mangles VON "Claude"-Familie** | `Claud` (standalone) → `Claude`, `Clot` → `Claude`, `Clude` → `Claude`, `Cloudcode` → `Claude Code` — **BEVOR** Cloud-Patterns laufen, damit keine Kollisionen entstehen |
| **4. Compound-Wort-Varianten** | `Cloud Desktop App` → `Claude Desktop App`, `Cloud App` → `Claude-App` |
| **5. Standalone "Cloud"-Fixe** | `\bCloud(?!e)\b` → `Claude` — letzter Pass, wenn alle Compounds schon erledigt sind |

Diese Reihenfolge garantiert:
- `Claud(?! Code)` (Pass 3) matcht nur die echten `Claud`-Stellen, nicht die durch Pass 4 produzierten `Claude Desktop App`-Stellen
- `\bCloud\b` (Pass 5) matcht nur noch echte standalone `Cloud`-Stellen, nicht mehr die Compounds

**Pflegetipp:** Immer die `Cloud`-Familie (Compound + Standalone) ZUM SCHLUSS patchen, nachdem alle `Claud`/`Clot`/`Clud`-Stellen bereits weg sind.

### ⚠️ Case-Insensitive Matching für Auto-Caption-Mangles

Auto-Captions sind inkonsistent in Groß-/Kleinschreibung. Ein typischer Bug: `\bClot\b` matcht im Input-Transkript nur 1 Stelle (`Clot Desktop App`), aber NICHT die lowercase-Variante `clot` an Satzanfang-mitte (`"der Server ist die ganze Zeit an und clot damit auch"`).

**Konsequenz:** Die `\bClot\b`-Variante wird gefixt, aber `clot` bleibt im Output und produziert einen UNSICHER-Eintrag.

**Lösung:** Auto-Caption-Mangle-Patterns IMMER case-insensitive schreiben:

```python
# FALSCH:
fix(r'\bClot\b',              'Claude')
fix(r'\bClot Desktop App\b',  'Claude Desktop App')

# RICHTIG:
fix(r'\b[Cc]lot\b',           'Claude')
fix(r'\b[Cc]lot Desktop App\b', 'Claude Desktop App')
```

**Faustregel:** Wenn das Pattern ein typischer Auto-Caption-Hörfehler ist (Tmax, Clot, Clud, SlashLOP, SLGal, ...) → IMMER case-insensitive. Bei korrekten Eigennamen (Hostinger, Anthropic) reicht case-sensitive, weil Auto-Captions sie meist richtig schreiben.

### ⚠️ Cross-Check gegen `input_raw_caption.txt` bei Unsicherheit

Bevor du einen `UNSICHER`-Eintrag produzierst: Lies die entsprechende Stelle in `input_raw_caption.txt` nach. Wenn die Roh-Caption den Begriff identisch (verhunzt) enthält, hat Julian genau das gesagt — und der Hörfehler bleibt unkorrigiert nur, wenn die Heuristik-Liste ihn nicht enthält. In dem Fall: in den UNSICHER-Block dokumentieren, nicht raten.

**Beispiel aus Session 2026-07-09 (pvhphecd70Y):**
- Input-Transkript hatte `"Cloud im DDatei anlegen"` — klingt nach Auto-Caption-Artefakt für `"Claude in 'ner Datei anlegen"`
- Raw-Caption bestätigt: `"eine Cloud im DDatei anlegen"` — Julian hat das genau so gesagt
- Heuristik-Liste enthält dieses Pattern NICHT
- → UNSICHER-Eintrag, NICHT automatisch zu `Claude in der Datei` korrigieren (wäre inhaltliche Änderung, nicht Eigennamen-Fix)

#### Häufigste Korrektur-Kategorien

**Tool-Name amputiert:**
| Caption | Korrekt | Kategorie |
|---------|---------|-----------|
| `Cloud Code` / `Claud Code` / `Clud Code` | `Claude Code` | Modell/Tool |
| `Cloud Cowork` / `Claud Cowork` / `Cloud Cow` | `Claude Cowork` | Modell/Tool |
| `OpenCla` / `OpenCl` / `Open Claw` | `OpenClaw` | Tool-Name (Julian Ivanov-Kanal) |
| `Clud` / `Clot` / `Clod` (standalone) | `Claude` | Modell-Name |
| `Claud` (standalone, nicht vor "Code"/"Cowork"/"ian") | `Claude` | Fehlendes 'e' |
| `Excalid Draw` / `Excaly Draw` / `Excalid Drop` / `Excalidrawrop` / `Excaly Drawrop` | `Excalidraw` | Tool-Name |
| `Brad Plugin` → (bleibt als Plugin) | `BRAT Plugin` | Obsidian-Plugin (nur falls BRAT-Kontext klar) |

**Rabattcodes / Plattformen:**
| Caption | Korrekt | Erklärung |
|---------|---------|-----------|
| `Jurian Ivanov` | `JULIANIVANOV` | Rabattcode, nicht Name |
| `Gitter Repository` | `GitHub-Repository` | 'Gitter' statt 'GitHub' |
| `Claudian Gitub` | `Claudian GitHub` | 'Gitub' statt 'GitHub' |

**JGPT → ChatGPT:**
| Caption | Korrekt | Erklärung |
|---------|---------|-----------|
| `JGPT` | `ChatGPT` | Auto-Caption tauscht 'Chat'-Laut gegen 'J' |

**Pro-Plan → Proan:**
| Caption | Korrekt | Erklärung |
|---------|---------|-----------|
| `Proan` | `Pro-Plan` | Fehlende 'Pl'-Silbe |

#### Standalone-Cloud-Disambiguierung (wichtig!)

Der Sprecher (besonders bei Julian-Ivanov-Videos) verwendet oft **"Cloud" als Kurzform für "Claude Code"** — z. B. "Hey Cloud, schreib mir..." oder "dann versteht Cloud, was ich meine". Das sind bis zu **49 Stellen** in einem 42-Minuten-Video.

Das Problem: **NICHT jedes "Cloud" im Transkript meint Claude Code.** In Obsidian-Kontexten kann "Cloud" tatsächlich Cloud-Storage bedeuten ("keine Cloud, keine Datenbank"). **Falsche Ersetzungen = inhaltlicher Fehler.**

**Disambiguierungs-Regeln (priorisiert):**

1. **"Cloud Code" (ohne Bindestrich)** → IMMER → "Claude Code". Das ist der häufigste 2-Wort-Hörfehler und nie ein echtes Cloud-Produkt.
2. **"Cloud-Code" (mit Bindestrich im Compound-Adjektiv)** → NIEMALS ersetzen. "Cloud-Code-Skill" = ein von Claude Code erstellter Skill, beschreibt den Urheber, kein Eigenname. Faustregel: Wenn Teil eines Bindestrich-Worts, nicht patchen.
3. **Standalone "Cloud" (alleinstehend)** → Kontext-abhängig:
   - **Im Claude-/Agent-Kontext** ("sag Cloud", "versteht Cloud", "Cloud zu ermöglichen") → "Claude" oder "Claude Code". Der Sprecher meint den Agenten.
   - **Im Infrastruktur-/Storage-Kontext** ("keine Cloud, keine Datenbank", "Cloud-Speicher") → "Cloud" belassen. Hier ist Cloud-Storage gemeint.
   - **In neutralen Passagen** (unklarer Kontext, isoliertes Vorkommen) → lieber "Claude" als sichere Annahme bei AI-Tutorials, aber in den UNSICHER-Block aufnehmen.
4. **"Cloud" + Tech-Wort am Satzanfang** → meist Claude. "Cloud installiert..." = Claude installiert.

**Praktische Umsetzung (in dieser Reihenfolge):**

```python
# Stufe 1: Immer ersetzen — Cloud Code / Cloud Cowork / Cloud Instanz
fix(r'\bCloud\s+Code\b',     'Claude Code',     'Cloud Code→Claude Code')
fix(r'\bCloud\s+Cowork\b',   'Claude Cowork',   'Cloud Cowork→Claude Cowork')
fix(r'\bCloud\s+Instanz\b',  'Claude-Instanz',  'Cloud Instanz→Claude-Instanz')

# Stufe 2: Standalone "Cloud" in Claude-Kontext — NACH den Compound-Fixes,
# damit "Cloud Code" nicht aufgespalten wird
# Nutze Lookahead für Claude-typische Verben/Kontext
fix(r'\bCloud\b(?=\s+(?:schreib|installier|erstell|sag|versteht|nutz|kann|mach))',
    'Claude', 'Cloud→Claude (vor Agent-Verb)')

# Stufe 3: Satzanfang "Cloud ..." im AI-Tutorial-Kontext → meist Claude
fix(r'\bCloud\b(?=\s+(?:ein|eine|den|die|das|nicht|auch|hier|dann|ja))',
    'Claude', 'Cloud→Claude (Satzstart im AI-Kontext)')

# Stufe 4: Residual — alle restlichen "Cloud" die nicht Infrastructure-Kontext haben
# DIESEN SCHRITT NUR AUSFÜHREN wenn Description den AI-Tutorial-Kontext bestätigt
# Alternative: als UNSICHER listen und vom Merger klären lassen
```

**Wichtig für den Merger:** Der Merger muss am Ende verifizieren, dass "Cloud" nicht doppelt ersetzt wurde (durch Worker 2 + Worker 1) und dass "Cloud-Speicher" / "Cloud-Infrastruktur" nicht fälschlich zu "Claude-Speicher" wurde.

### 4. UNSICHER dokumentieren (nicht korrigieren)

Manche Wörter klingen nach Hörfehlern, sind aber nicht eindeutig identifizierbar. Diese **niemals automatisch korrigieren**, sondern dokumentieren.

**Kriterien für UNSICHER:**
- Das Wort kommt nur 1-2x vor (kein Muster erkennbar)
- Der Kontext erlaubt mehrere Interpretationen
- Die Description gibt keinen eindeutigen Hinweis
- Es könnte ein seltener Tool-Name oder Slang sein

**Output-Format für unsichere Fälle:**
```text
===UNSICHER===
- '<wort>' (Nx) — <Kontext aus Transkript>, wahrscheinlich <Vermutung>, aber nicht in Liste, unverändert lassen
```

**Beispiele aus der Praxis (alle unverändert gelassen):**
| Wort | Kontext | Vermutung | Grund für Unsicherheit |
|------|---------|-----------|----------------------|
| `Trujah` | "dass das Trujah viel zu teuer sei" | Tool | Keine Treffer in Description, nur 1x |
| `NAN` | "in der NAN haben wir deutlich mehr Transparenz" | N8N | N8N kommt im Kontext vor, aber 'NAN' könnte auch anders sein |
| `Routro` | "open Routro/" | Router | OpenRouter-API, aber Verhunzung zu unspezifisch |
| `lavable` | "über lavable" | Lovable | AI-App-Builder, nur 1x |
| `WT` / `VT` / `Volt` (15x) | "neuen WT erstellen" | Vault (Obsidian-Terminus) | Vault ist Obsidian-Ordner, aber WT/VT/Volt sind inkonsistente Hörfehler |
| `Grafansicht` (2x) | "diese Grafansicht" | Graph View | Ein Wort statt zwei, aber unklar ob beabsichtigt |
| `Claw` (als Eigenname) | "ich setze hier für sowas immer auf Sonnet oder auch Opus. Sonet wird jetzt auf jeden Fall ausreichen" | Tool | Im Kontext von Modellauswahl, könnte auch als Anrede gemeint sein |
| `Notizapp` (1x) | "in einer Notizapp" | Notiz-App | Zusammenschreibung, wahrscheinlich korrekt |
| `Zahnrad` (1x) | "hier unten links auf das Zahnrad" | Zahnrad (UI-Metapher) | Obsidian-UI-Begriff, kein Hörfehler — korrekt |
| `Proan` (2x) | "im Proan" | Pro-Plan | Abonnements-Stufe |
| `Claudian Gitub` | "das Claudian Gitub Repository" | Claudian GitHub | Beide Begriffe verhunzt — von Description getrennt prüfen |
| `Chat GBT` | "von JGPT zu Cloud wechselst" | ChatGPT | Zwei Varianten im Video: Chat GBT + JGPT |
| `dass ihr hier` | "dass ihr hier immer solche Gedankenstriche nutzt" | Grammatik | Hörfehler im Relativsatz (gehört zu Worker 1) |

### 5. Output schreiben

**Standard-Variante:** Datei `/tmp/yt_polish_output_stil.md`

```text
===START_STIL===
<polieter text>
===END_STIL===
```

Die Marker sind zwingend — der Merger parst sie, um Worker-1/2/3-Output zu unterscheiden.

**Swarm-Variante:** Datei `/tmp/yt_remote_workers/output_worker2_stil.md`

```text
===START_WORKER2_STIL===
<korrigierter text>
===END_WORKER2_STIL===
===STATUS_WORKER2_STIL===
Woerter: NNNN
Eingabe-Woerter: NNNN
Gefixt:
  - <Begriff_A>: Nx
  - <Begriff_B>: Mx
Minuten-Marker: N/Total
Wort-Drift: +/-X% (Limit +-3%)
[UNSICHER (residue nach allen Passes, manuelle Pruefung empfohlen):
  - <Begriff>: Nx -> samples=[<samples>]]
===END_STATUS_WORKER2_STIL===
```

**Unterschiede zur Standard-Variante:**

| Aspekt | Standard | Swarm |
|--------|----------|-------|
| Marker | `===START_STIL===` | `===START_WORKER2_STIL===` (worker-spezifisch, damit Merger/Orchestrator sie auseinanderhält) |
| Status | Optional, einfache Liste | **Zwingend**, strukturierter Block mit Wortzahl + Drift + Marker-Count + ggf. UNSICHER-Liste |
| Drift-Limit | 2% (Worker 2 hat Spielraum) | **±3%** (vom Orchestrator vorgegeben, weil Worker 2 nur Eigennamen-Fixes macht — Drift sollte nahe 0% sein) |
| Pflicht-Assertions | Wortzahl-Drift-Check | Wortzahl-Drift + Marker-Count + **`Claudee`-Over-Substitution-Check** (siehe unten) |

**Wort-Drift-Realität (Swarm-Variante, Session 2026-07-09):** Eigennamen-Fixes sind zeichenlängen-neutral (`Tmax`=4 Buchstaben, `tmux`=4 → keine Drift; `SlashG`=6, `/goal`=5 → -1 Zeichen; `Cloud`=5, `Claude`=6 → +1 Zeichen). Beim 4906-Wörter-Run pvhphecd70Y lag die finale Drift bei **-0.08%** — weit unter dem 3%-Limit. Drift-Werte >1% sind verdächtig und deuten auf einen Pattern-Bug hin.

### ⚠️ Pflicht-Assertion: `Claudee`-Over-Substitution-Check

**Symptom:** Wenn ein Standalone-Pattern wie `Claud` → `Claude` zusammen mit Compound-Form-Patterns wie `Cloud Desktop App` → `Claude Desktop App` in falscher Reihenfolge läuft, entsteht **doppeltes 'e'**: `Claudee Desktop App`.

**Erkennung:**
```python
assert 'Claudee' not in txt, "Bug: 'Claudee' detected (double-e from overlapping passes)"
```

Diese Assertion MUSS am Ende jedes Worker-2-Runs stehen, BEVOR der Output geschrieben wird. Wenn sie feuert: Reihenfolge der Passes prüfen (siehe Pass-Ordering-Falle oben) und nochmal von vorne.

**Generalisierung:** Auch für andere "doppelte-Buchstaben"-Risiken checken:
- `ClaudeCode` (ohne Space — `Claude Code` → `ClaudeCode` falls Pattern zu eng wird)
- `CLAUDEMD` (ohne Punkt — `CLAUDE.md` → `CLAUDEMD`)
- `tmuxt` (Tippfehler durch ähnliche Patterns)

**Defense-in-Depth:** Zusätzlich zur Assertion eine Regex-Suche über alle Patterns laufen lassen, die "das Wort X gefolgt von X nochmal" oder "Wort gefolgt von himself" detektiert — kostet <100ms bei einem 50KB-Transkript.

### 6. Status-Block dokumentieren

Zusätzlich zum Output einen Status-Block ans Datei-Ende **oder** auf stdout ausgeben:

```text
===FIXES===
OpenCla→OpenClaw: 20x
Cloud Code→Claude Code: 7x
...
TOTAL: 78

===ALL_FIXED===   # oder ===REMAINING=== wenn Patterns ungefixt blieben

===UNSICHER===
- Trujah (1x) — ...
- ... (Nx) — ...
```

**Erweiterte Selbst-Verifikation (zwingend) — in zwei Stufen:**

```python
import re

# Stufe A: Prüfen ob noch unkorrigierte Ziel-Patterns existieren
remaining = []
for pattern in [r'\bOpenCla\b', r'\bOpenCl\b', r'\bCloud Opus\b', ...]:
    matches = re.findall(pattern, poliert)
    if matches:
        remaining.append(f"{pattern}: {matches}")

if remaining:
    print("===REMAINING===" + "\n".join(remaining))
else:
    print("===ALL_FIXED===")

# Stufe B: Word-Count-Drift prüfen (sollte < 2% sein, erwartbar leicht negativ durch Compound-Merges)
import re
original_wc = len(re.findall(r"\S+", original_text))
polished_wc = len(re.findall(r"\S+", poliert))
drift = ((polished_wc - original_wc) / original_wc) * 100
print(f"Wortzahl-Drift: {drift:.2f}% ({original_wc} → {polished_wc})")
# Typisch: -0.04% bis -1.6% (je nach Compound-Fix-Dichte)
# Warnung bei > 2% Abweichung
if abs(drift) > 2:
    print("⚠️  WARNUNG: Wortzahl-Drift > 2% — möglicher Content-Verlust durch zu aggressive Ersetzung!")
```

## Fehler, die NICHT zu Worker 2 gehören

Worker 2 korrigiert NUR Eigennamen + Fachbegriffe. Folgendes gehört **nicht** hierher:

| Was | Gehört zu | Begründung |
|-----|-----------|------------|
| Satzzeichen setzen | Worker 1 (Inhalt) | Sprachliche Glättung |
| Absatz-Struktur | Worker 1 (Inhalt) | Formatierung |
| Füllwort-Entfernung | ✗ Gar nicht | Gehört zum Sprachstil |
| Inhaltliche Korrekturen | Worker 3 (Faktencheck) | z. B. falsche Modell-Info |
| Fakten-Prüfung | Worker 3 (Faktencheck) | Description vs. Transkript |
| Compound-Word-Varianten prüfen | **Merger** (nach dem Merge) | z. B. MCPS vs. MCP-Server |

## Channel-spezifische Notes

Verschiedene YouTuber haben unterschiedliche Themen-Schwerpunkte, die eigene Hörfehler-Muster produzieren:

| Kanal / Nische | Häufige Begriffe | Typische Hörfehler |
|----------------|------------------|-------------------|
| **Julian Ivanov** (OpenClaw-Tutorials) | OpenClaw, N8N, Claude Code, VPS, Telegram CLI | OpenCla→OpenClaw, Claw-Verhunzungen, Agent-Patterns |
| **Hive Mind** (Obsidian+Claude-Setup) | Obsidian, Excalidraw, Claude Cowork, Second Brain, CLAUDE.md | Excalidraw-Varianten, Cloud Cowork→Claude Cowork, Claudian, JGPT, Proan |
| **Allgemeine AI-Tutorials** | Claude Code, ChatGPT, API-Keys, Memory | Cloud→Claude, JGPT→ChatGPT, API-Key-Verhunzungen |

Die Pattern-Matrix in `known-hearing-errors.md` wächst mit jedem neuen Kanal und sollte kanalunabhängig viele Patterns abdecken.

## Output-Philosophie

**"Wenn unsicher, lass es stehen"** — Lieber ein unkorrigiertes Wort als eine falsche Korrektur. Jeder nicht gefixte Fall wird im `UNSICHER`-Block dokumentiert, so dass der Merger und Worker 3 entscheiden können.

**Verifizieren vor dem Abschluss:** Immer prüfen ob alle Ziel-Patterns tatsächlich verschwunden sind. Die `===ALL_FIXED===` / `===REMAINING===`-Prüfung ist keine Kür, sondern ein Quality Gate.

**Wortzahl-Drift als Indikator:** Ein Drift von 0.5-1.5% nach unten ist normal (Compound-Merges fassen mehrere Wörter zu einem zusammen, z.B. "Cloud Cowork" → "Claude Cowork"). Ein Drift > 2% ist verdächtig und sollte vor Abgabe geprüft werden.

## Siehe auch

- `known-hearing-errors.md` — Vollständige Regex-Such-Matrix mit P0/P1/P2-Klassifikation
- `SKILL.md` → Stufe 3 — Multi-Agent-Pipeline-Übersicht und Merger-Pitfalls
- `faktencheck-methodology.md` — Worker 3 (läuft parallel zu Worker 2)
- `SKILL.md` → Pitfall "Stufe-0-Pass hat systematische Lücken" — warum die Post-Polish-Verifikation auch im Swarm-Setup Pflicht ist
- `SKILL.md` → Pitfall "Slash-Regex mit \\b-Word-Boundary funktioniert NICHT für `/loop`, `/goal`" — für die Verifikations-Snippets beim Slash-Command-Check

## Changelog

- **2026-07-09**: Swarm-Variante dokumentiert (Context.md-Eingabe, Output-Wrapper `===START_WORKER2_STIL===` + zwingender Status-Block). Drei neue Pflicht-Pitfalls hinzugefügt: Pass-Ordering-Falle (Compound vs. Standalone), Case-Insensitive Matching für Auto-Caption-Mangles, `Claudee`-Over-Substitution-Assertion. Cross-Check-Snippet gegen `input_raw_caption.txt` ergänzt.

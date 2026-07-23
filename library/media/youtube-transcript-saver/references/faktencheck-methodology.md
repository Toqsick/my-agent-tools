# Faktencheck-Methodik (Worker 3)

## Wann einsetzen

Worker 3 (Faktencheck) ist der dritte parallele Worker in Stufe 3 der Caption-Polishing-Pipeline.
Er läuft **parallel** zu Worker 1 (Inhalt/Sprache) und Worker 2 (Stil/Eigennamen) und wird erst nach Fertigstellung aller drei Worker durch den Merger zusammengeführt.

Seine Aufgabe: **NICHT** den Text polieren, sondern **das Transkript systematisch gegen die YouTube-Description (Titel, Channel, Upload-Datum, Beschreibung, Lernziele, Links, Zeitstempel, Tags) validieren** und einen strukturierten Report mit Inkonsistenzen, Auto-Caption-Hörfehlern und Handlungsempfehlungen schreiben.

## Inputs

Worker 3 hat immer ZWEI Eingabedateien:

| Datei | Inhalt |
|-------|--------|
| `/tmp/yt_polish_input.txt` | Roh-Transkript (eine Zeile, ~30 KB, keine Formatierung) |
| `/tmp/yt_polish_description.txt` | YouTube-Description (Titel, Channel, Upload, Dauer, Views, Beschreibung, Lernziele, Links, Zeitstempel, Tags) |

## Workflow (Schritt für Schritt)

### 1. Beide Inputs lesen

```python
# Struktur-Erkennung: ist das Transkript eine einzelne lange Zeile?
# read_file zeigt Zeile 1|...am Anfang... und ggf. tail am Ende
# Dann: Volltextsuche per grep, NICHT per Python read (wegen single-line)
```

Wenn `read_file` das Transkript als 0 Zeilen oder nur 1 Zeile anzeigt, ist es ein Single-Line-File.
In dem Fall **kein Python-Read** (würde 30 KB in eine Zeile laden) — stattdessen `grep -oP` mit Regex im Terminal.

### 1b. Alternative Primärquelle: JSON-Segments-Datei (empfohlen, falls vorhanden)

Die Pipeline produziert oft eine strukturierte JSON-Segments-Datei unter `/tmp/yt_v*_segments.json` (oder direkt aus dem Caption-Api-Skript). Diese Datei ist DEUTLICH präziser als der flache Text-Blob:

```json
[
  {"start": 0.199, "duration": 3.401, "text": "In diesem Video zeige ich dir, wie du"},
  {"start": 1.599, "duration": 4.68,  "text": "dir dein eigenes KI Betriebssystem"},
  ...
]
```

**Auffinden:**
```bash
ls /tmp/yt_v*_segments.json 2>/dev/null
ls /tmp/*segments.json 2>/dev/null
```

**Python-Setup für die Analyse:**

```python
import json, re
with open('/tmp/yt_v6_segments.json') as f:
    data = json.load(f)

# Volltext aus allen Segmenten
full_text = ' '.join(seg['text'] for seg in data)

# Letzte Position = Dauer
total_duration = data[-1]['start'] + data[-1]['duration']

# Zeitformat-Konverter
def fmt(seconds):
    return f"{int(seconds)//60:02d}:{int(seconds)%60:02d}"
```

**Vorteile gegenüber grep-basiertem Workflow:**

| Aspekt | grep auf Single-Line-Blob | JSON-Segments-Analyse |
|--------|--------------------------|----------------------|
| **Treffer-Zählung** | `grep -oP 'pattern' \| wc -l` — akzeptabel | `full_text.lower().count('pattern')` — exakt |
| **Kontext zu Treffern** | `grep -oP '.{60}pattern.{60}'` — funktioniert | `re.findall(r'.{60}pattern.{60}', full_text)` — identisch |
| **Zeitstempel** | Nicht enthalten (nur Text) | Jedes Segment hat `.start` + `.duration` |
| **Begriffs-Varianten-Entdeckung** | Nur manuell per mehreren grep-Aufrufen | Automatisch: `set(re.findall(r'\bC[cl]o[loud]+\w*\b', full_text))` |
| **Aggregierte Statistiken** | Mehrere Shell-Durchläufe | Ein Python-Durchlauf mit dict/set — viele Patterns gleichzeitig |
| **Kapiteleinteilung** | Nicht vorhanden | Nach `start` sortierte Segmente — Positionsanalyse auf Sekunden-Ebene |

**Praktischer Workflow — Pattern-Familien in einem Durchlauf identifizieren:**

```python
# === Schritt 1: Alle Varianten einer Begriffsfamilie finden ===
cloud_variants = set(re.findall(r'\b[Cc]lou?[ud][a-z]*\b', full_text))
print(sorted(cloud_variants))
# → ['Cloud', 'Cloudnutzung', 'Cloudspeicher', 'cloud']

# === Schritt 2: Exakte Treffer pro Kategorie zählen ===
kategorien = {
    'Cloud Code': r'\bCloud Code\b',
    'Claud': r'\bClaud\b',
    'Clot': r'\bClot\b',
    'Clotter': r'\bClotter\b',
    'Cloudnutzung': r'\bCloudnutzung\b',
    'Cloud MDI': r'\bCloud [MD]{2,3}\b',
    'Cloud im DD': r'Cloud im DDatei',
}
for label, pat in kategorien.items():
    matches = re.findall(pat, full_text, re.IGNORECASE)
    print(f'{label:20s}: {len(matches)}x   -> {matches[:3]}')

# === Schritt 3: Kontext-Extraktion für jede Kategorie ===
context_matches = re.findall(r'.{60}Claud.{60}', full_text)
for m in context_matches[:5]:
    print(repr(m))
```

**Pitfall: Datei-Encoding und Zeilenstruktur checken.**  
Manche JSON-Dateien sind 1-Zeile (kompaktes JSON). `cat` zeigt alles — das ist OK. JSON-Parser wie `json.load()` lesen trotzdem korrekt. Bei Dateien >500 KB reichen die ersten 200 Segmente für eine repräsentative Analyse.

**Wann JSON statt grep nutzen:** IMMER wenn vorhanden — es ist strikt besser als der flache Blob. NUR wenn nicht vorhanden auf grep-Basis ausweichen.

**Wann beide parallel nutzen:** Für die Endvalidierung: JSON-Segments für Timestamp-Präzision, grep auf Blob für Wort-für-Wort-Konsistenz. Kreuzvalidierung: gleiche Trefferzahl in beiden Quellen → konsistent.

### 2. Systematische Keyword-Suche (grep-basiert)

Für jeden Begriff aus der Description (Tags, Tools, Modelle, Lernziele, Themen) eine gezielte grep-Suche:

```bash
# Exakte Wort-Suche mit Wortgrenzen
grep -oP '\b[Tt]erm\b' /tmp/yt_polish_input.txt | sort -u

# Mit Zählung
grep -oP '\b[Tt]erm\b' /tmp/yt_polish_input.txt | wc -l

# Mit umgebendem Kontext (60 Zeichen links/rechts)
grep -oP '.{60}[Tt]erm.{60}' /tmp/yt_polish_input.txt
```

**Kontext ist entscheidend!** Die nackte Trefferzahl reicht nicht — der Kontext sagt dir, ob der Begriff korrekt verwendet wird (z. B. "Telegram" als Slash-Befehl vs. als Messaging-Kanal).

### 3. Cross-Reference: Description-Tags → Transkript

Jeden einzelnen Tag aus der Description nehmen und prüfen:

| Tag (z. B. aus Description) | Prüfung im Transkript | Mögliche Diskrepanz |
|----------------------------|----------------------|---------------------|
| Tool-Name "OpenClaw" | Existiert das Wort? In welcher Form? (OpenCla? OpenClaw? OpenCl?) | Hörfehler amputieren den Namen |
| Modell "Claude Opus 4.5" | Wird es erwähnt? In welcher Schreibweise? | Cloud Opos, Spiel Cloud Opus |
| Plattform "Telegram" | Als Messaging-Kanal oder als Slash-Befehl? | `/models`-Befehl != Telegram-Bot |
| Hosting "VPS" | Kommt "VPS" wörtlich vor? | Oft nur "Hostinger"/"Server" |
| Synonyme "Clawdbot"/"Moltbot" | Kommen sie vor? | Im Transkript meist nur "OpenClaw" |

### 4. Zeitstempel-Check

Wenn die Description Zeitstempel-Kapitel hat (00:00, 02:14, etc.):

```bash
# Alle Zeitstempel-artigen Patterns finden
grep -oP '\d{1,2}:\d{2}' /tmp/yt_polish_input.txt | sort -u
```

Prüfen:
- Stimmen die Kapitelübergänge mit der Description überein?
- Fehlen Kapitel aus der Description?
- Gibt es zusätzliche Kapitel im Transkript?

### 4a. Erweiterte Methode: Positional-Analysis (Character-Position-%)

Wenn das Transkript **keine eigenen Zeitstempel enthält** (häufig bei Auto-Captions aus `youtube-transcript-api` ohne Timestamp-Export), funktioniert der Standard-Grep nicht.

**Lösung: Charakter-Positions-%-Analyse**

Prinzip: Jeder Topic-Sektion im Transkript wird ihre relative Position als Prozentsatz der Gesamttextlänge zugeordnet. Dieser Prozentsatz wird mit der relativen Position des Description-Zeitstempels verglichen: `(timestamp_minuten / gesamtdauer_minuten) * 100`.

```python
c = gesamter_transkript_text  # ein String
laenge = len(c)

# Eindeutige Anchor-Phrasen pro Description-Kapitel wählen
anchor_phrases = {
    "Einleitung": "Das hier ist",
    "5 Vorteile": "fünf der wichtigsten Vorteile",
    "Setup": "Wir gehen jetzt in das Setup",
    # ...
}

for label, phrase in anchor_phrases.items():
    idx = c.find(phrase)
    if idx >= 0:
        transcript_pct = idx / laenge * 100
        print(f"{label}: {transcript_pct:.1f}%")
```

**Abgleich mit Description-Zeitstempeln:**

```python
# Beispiel: Video-Dauer = 36:24 = 36.4 Minuten
video_dauer_min = 36.4
desc_kapitel = {"Einleitung": 0.0, "5 Vorteile": 3.03, "Setup": 10.58}

for kapitel, desc_min in desc_kapitel.items():
    desc_pct = desc_min / video_dauer_min * 100  # z.B. 3.03/36.4 = 8.3%
    differenz = abs(transcript_pct - desc_pct)
    if differenz < 5:   status = "✅ konsistent"
    elif differenz < 10: status = "⚠ grenzwertig"
    else:                 status = "❌ Abweichung"
```

**Plausibilitäts-Toleranz:**
- `±5 Prozentpunkte` = konsistent (ein bei 30% erwartetes Thema darf zwischen 25–35% liegen)
- `±5–10 Prozentpunkte` = grenzwertig (im Report vermerken, aber nicht als Fehler werten)
- `>10 Prozentpunkte` = Warnung (Topic liegt deutlich verspätet/verfrüht)

**Vorteile gegenüber reinem Grep:**
- Funktioniert auch wenn das Transkript **gar keine Timestamps** hat
- Gibt eine **quantifizierbare Metrik** für Zeitstempel-Konsistenz
- Erzeugt eine nachvollziehbare Tabelle für den Merger

**Wann verwenden:** Immer wenn das Transkript keine Timestamps enthält (häufig bei Single-Line-Auto-Captions). Bei Transkripten mit Timestamps reicht der Standard-Grep.

**Pitfall: Anchor-Phrase muss eindeutig sein.** `"Vorteile"` ist zu vage — `"fünf der wichtigsten Vorteile"` ist einmalig. Zweideutige Phrasen produzieren falsche Positionen. Vor der Analyse mit `grep -oP` prüfen ob die Phrase nur einmal vorkommt.

### 4b. Description-Kapitel-Completeness (Vollständigkeit der Kapitelliste)

Nicht jede YouTube-Description listet ALLE Kapitel mit Zeitstempeln auf. Häufig sind die letzten Kapitel als "_(weitere)_" markiert oder fehlen komplett. **Das ist kein Fehler** des Transkripts — der Creator hat sie schlicht nicht getimt.

**Vorgehen:**
1. Aus der Description die **Anzahl der nummerierten Items** extrahieren (z. B. "Top 10" = 10 Items)
2. Die **Anzahl der expliziten Zeitstempel** in der Description zählen
3. Differenz feststellen: `N_Items - N_Timestamps = Fehlende_Zeitstempel`
4. Wenn Fehlende_Zeitstempel > 1 → Notiz im Report: "Description listet nur N/M Kapiteln mit Zeitstempeln, restliche mit _(weitere)_ — Transkript-Daten können ergänzen"

```python
# Beispiel: 10 Items in Description, aber nur 8 Timestamps
diff = 10 - len(desc_timestamps)  # = 2
# Die 2 fehlenden sind typischerweise die letzten Kapitel:
# #9 Superpowers ~36:00, #10 CLAUDE.md Management ~40:23
```

**Im Report flaggen:** `DESCRIPTION_TIMESTAMPS_VOLLSTAENDIG: nein (N/M)`

### 4c. Timestamp-Drift-Analyse für einzelne Kapitel

Jedes Description-Kapitel mit Zeitstempel gegen die tatsächliche Transkript-Position validieren. Anders als die globale Posititions-%-Analyse aus 4a, geht es hier um den **Erstbeleg des Tool-Namens oder der Kapitelübergangsphrase** im Transkript, verglichen mit dem Description-Zeitstempel.

**Vorgehen:**
1. Für jedes Description-Kapitel den Tool-Namen oder die Übergangsphrase nehmen
2. Im Transkript mit Segment-Timestamps den frühesten Beleg finden (bei vorhandenen Segment-JSON)
3. Mit Description-Zeitstempel vergleichen

```python
# Beispiel aus Transkript mit Segment-JSON
drift = {
    "Excalidraw":   0,       # Description 03:51 ↔ Transkript 03:51 ✓
    "NotebookLM":   2,       # Description 07:53 ↔ Transkript 07:55 (+2s) ✓
    "Firecrawl":   32,       # Description 20:51 ↔ Transkript 21:23 (+32s) ⚠ grenzwertig
}
```

**Toleranz:**
- `±5 Sekunden` = perfekt
- `±5–30 Sekunden` = akzeptabel (der Sprecher kann ein Thema vor dem Tool-Namen anreißen)
- `>30 Sekunden` = im Report flaggen

**Wichtige Nuance:** Der erste Beleg des Tool-Namens kann im **Kapitelübergang** selbst liegen (der Sprecher sagt "Kommen wir zu Nummer X, das ist der {Toolname}-Skill") ODER erst später, wenn er den Tool-Namen im laufenden Text nennt. Die Drift zum Description-Zeitstempel bezieht sich daher auf das **erste Auftreten des Tool-Namens im Transkript**, nicht auf die Kapitel-Übergangsphrase.

### 5. Lernziele / Hauptthemen abdecken

Jedes Lernziel aus der Description einzeln checken. Schnell-Methode:

```bash
for topic in "Morgenbriefing" "Tagebuch" "Competitoranalyse" "Kosten" "Community"; do
    count=$(grep -oP "$topic" /tmp/yt_polish_input.txt | wc -l)
    echo "$topic: $count Treffer"
done
```

Wenn ein Thema 0 Treffer hat → Fehlanzeige im Report.
Wenn ein Thema <2 Treffer hat → nur gestreift, nicht vertieft.

### 5a. Strukturierte Topic-Coverage-Tabelle (empfohlen für >5 Themen)

Bei mehr als 5 Hauptthemen oder wenn die Description eine nummerierte Liste hat, ist die einfache grep-Zählung zu grob. Stattdessen eine **strukturierte Tabelle pro Hauptthema**:

| # | Hauptthema (Description) | Transkript-Nachweis | Status |
|---|---|---|---|
| 1 | 5 Vorteile | "Das erste ist…" + "Der zweite Punkt…" + "Der fünfte Vorteil…" — alle 5 Punkte mit Ordnungszahlworten | ✅ vollständig |
| 2 | Setup (Obsidian) | "Wir gehen jetzt in das Setup" — Obsidian-Download, Vault erstellen, BRAT-Plugin | ✅ vollständig |
| 3 | Theme anpassen | "Darstellung auf Thema… Anup Puuccin" — Theme-Installation + Customization | ✅ vollständig |

**Status-Optionen:**
- `✅ vollständig` — Thema mit allen Sub-Punkten nachweisbar
- `⚠︎ teilweise` — Thema vorhanden aber lückenhaft (z. B. nur 3 von 5 Tipps nachweisbar)
- `❌ fehlt` — Thema im Transkript nicht auffindbar (Description hat es, Transkript nicht)

**Nachweis-Suche:**
1. Eindeutige Anchor-Phrase finden (z. B. Ordnungszahlwörter für nummerierte Listen)
2. Bei nummerierten Listen: alle Elemente einzeln nachweisen (z. B. 5x "Der ... ist" bei 5 Vorteilen)
3. Kontext-Extraktion mit `grep -oP '.{100}Suchphrase.{200}'`

**Pitfall: Anchor-Phrasen müssen Description exakt widerspiegeln.** Ein Description-Kapitel "Setup" kann im Transkript als "Installation" oder "Einrichtung" auftauchen — nach allen drei Varianten suchen.

### 5b. Attribution-Verification (Creator/Copyright-Check)

Viele YouTube-Descriptions enthalten Creator-Attributionen: "von kepano", "von obra", "von Upstash", "von Cole Medin". Diese sind wichtig für die korrekte Quellenangabe im polierten Transkript. **Der Faktencheck muss prüfen, ob diese Attributionen im Transkript tatsächlich fallen.**

**Vorgehen:**
1. Aus der Description alle Creator-/Copyright-Hinweise extrahieren (Muster: "von X", "by X", "X hat entwickelt", Repo-Links mit Usernamen)
2. Jeden Creator-Namen im Transkript suchen:
   ```bash
   grep -oP 'kepano|obra|Upstash|Cole Medin|Col Medin|Coledien' /tmp/yt_polish_input.txt
   ```
3. Status-Code pro Creator:
   - `✅ wörtlich` — Name erscheint korrekt im Transkript
   - `⚠︎ ASR-verzerrt` — Name ist erkennbar aber verstümmelt (z. B. "Coledien" → "Cole Medin")
   - `❌ akustisch fehlend` — Name erscheint NIRGENDS im Transkript (auch nicht in verzerrter Form)

**Praktisches Beispiel aus Session 2026-07-04-b (Top 10 Claude Code Skills):**

| Creator | In Description | Im Transkript | Status |
|---------|---------------|---------------|--------|
| Cole Medin | Excalidraw Skill-Autor | "Col Medin" / "Coledien" (04:43) | ⚠ ASR-verzerrt |
| Microsoft | Playwright CLI | Nicht explizit im Transkript (nur "Microsoft hat… CLI veröffentlicht") | ✅ implizit |
| Anthropic | Feature Dev Plugin + CLAUDE.md | "Feature Death" (33:04), "Cloud MD Management" (40:23) | ⚠ ASR-verzerrt |
| kepano | Obsidian Skills | **Kein Treffer** im Transkript (nur "Repository heißt Obsidian Skills") | ❌ akustisch fehlend |
| obra | Superpowers Plugin | **Kein Treffer** im Transkript | ❌ akustisch fehlend |
| Upstash | Context7 | **Kein Treffer** im Transkript (nur "Context7 im Dashboard") | ❌ akustisch fehlend |

**Konsequenz für den Merger:** Creator-Namen die ❌ sind, können nicht automatisch aus dem Transkript gefixt werden. Sie müssen aus der Description in den Merge-Output übernommen werden (z. B. als "Repository von kepano (github.com/kepano/obsidian-skills)").

### 6. Auto-Caption-Hörfehler katalogisieren

Nach den bekannten Mustern aus `known-hearing-errors.md` suchen, **plus** neue Muster identifizieren:

**Häufigste Kategorien:**
1. **Tool-Namen amputiert**: OpenClaw → OpenCla, OpenCl, OpenClore
2. **Modellnamen verhunzt**: Claude Opus → Cloud Opos, Cloudsonet → Sonnet
3. **Fachbegriffe falsch**: Outlier → Outlayer, Heartbeat → Heardbeat
4. **Buchstaben-getauscht**: ChatGPT → Chat GBT, Anthropic → Anthopic
5. **Wort-Zusammenklebungen**: OpenClaufgaben, Not1Schritt
6. **Auto-Caption-Artefakte**: [räuspern], Spiel Cloud Opus (überflüssiges "Spiel")
7. **Rabattcodes/Fremdwörter**: Jurian Ivanov → JULIANIVANOV
8. **Tools der Auto-Caption unverständlich**: Trujah (unklarer Tool-Name)

**Neue Muster erkennen:**
- Nach bekannten Tool-Namen suchen, die im Transkript anders aussehen
- Nach phonetischen Ähnlichkeiten zwischen Description-Text und Transkript-Text
- Besonders bei englischen Begriffen in deutschem Auto-Caption: deutschsprachige Hörfehler

### 7. Report schreiben

Output-Datei: `/tmp/yt_polish_output_faktencheck.md`

Report-Struktur:

```markdown
# Faktencheck-Report — Transkript vs. YouTube-Description

**Video:** <Titel>
**Upload:** <Datum> · **Dauer:** <HH:MM> · **Views:** <N>
**Worker:** 3/3 (Faktencheck, keine Textänderungen)

---

===FAKTENCHECK_REPORT===
KONSISTENZ: <OK|WARN|FAIL>
USECASES_5_VOLLSTAENDIG: <ja|nein>
ZEITSTEMPEL_KONSISTENT: <ja|nein>
TOOLS_ERWAEHNT: <Liste aller Tools/Modelle mit Trefferzahlen>
HAUPTTHEMEN_ABDECKUNG: <Prozent> — <Detail>
WIDERSPRUECHE:
- <Diskrepanz 1 mit Erklärung>
- <Diskrepanz 2 mit Erklärung>
AUFFAELLIGKEITEN:
<nummerierte Liste aller Auto-Caption-Hörfehler>
EMPFEHLUNG:
- <Handlungsempfehlungen für Merger/Worker 2>
===END_REPORT===
```

### 8. Empfehlungen für Merger

Der Merger liest den Faktencheck-Report und entscheidet:
- **Welche Hörfehler**: Worker 2 (Stil) hat viele vermutlich schon gefixt, aber der Faktencheck liefert die, die Worker 2 übersehen hat
- **Welche Widersprüche**: Description-Tags die nicht zum Transkript passen (z. B. "Telegram" als Tag, aber nur `/models`-Befehl im Transkript)
- **Welche Compound-Varianten**: Der Merger muss nach dem Mergen spezifische Compound-Word-Varianten checken (siehe `known-hearing-errors.md`)

## Output-Convention

Worker schreibt sein Ergebnis nach `/tmp/yt_polish_output_faktencheck.md` **ohne** `===START===` / `===END===`-Wrapper (anders als Worker 1+2), da der Faktencheck-Report nicht direkt in den Merged-Text eingebaut wird, sondern als **Quality-Gate** dient.

**Wichtig (Update Session 2026-07-09):** In Schwarm-Setups (`templates/stufe3_schwarm_input_layout.md`)
sollte Worker 3 den gleichen `===START_FAKTENCHECK===` / `===END_FAKTENCHECK===` Wrapper
verwenden wie die anderen Worker, damit der Merger die Findings parsen kann. Wrapper ist
explizit im Delegation-Prompt definiert (`templates/stufe3_schwarm_delegation_prompts.md` →
FAKTENCHECK_PROMPT).

## Pitfalls

### ⚠️ Single-Line-Transkripte

YouTube-Auto-Captions kommen oft als eine einzige Zeile ohne Zeilenumbrüche. Dann:
- `read_file` zeigt `1|` gefolgt vom Anfang (wenn <2000 Zeilen)
- `grep` mit `-oP` funktioniert trotzdem — Regex matched im gesamten Text
- `wc -l` zeigt 1 oder 0 Zeilen → das ist der Hinweis!
- Kontext-Extraktion mit `grep -oP '.{60}Muster.{60}'` funktioniert auch in single-line files

### ⚠️ Description-Tags sind nicht immer im Transkript

Tags wie "VPS", "Telegram", "Clawdbot", "Moltbot" können in der Description stehen, aber im Transkript NICHT vorkommen. Das ist kein Transkript-Fehler — der YouTuber hat sie als Meta-Tags gesetzt, ohne sie im Video auszusprechen.

**Trotzdem im Report flaggen** mit Erklärung, damit der Merger entscheiden kann:
- Tag beibehalten (weil das Thema vom Hosting abgedeckt wird, nur nicht das Wort "VPS")
- Tag streichen (weil komplett inexistent, z. B. Clawdbot/Moltbot)
- Tag umformulieren (z. B. "Telegram" → "OpenClaw-CLI /models Befehl")

### ⚠️ Hörfehler ≠ inhaltliches Problem

Nicht jeder Auto-Caption-Hörfehler ist ein inhaltlicher Widerspruch.
`"Cloud Opos 4.6"` → gemeint ist `"Claude Opus 4.6"`, das ist inhaltlich korrekt, nur die Schreibweise ist falsch.

Der Report muss trennen:
- **Widersprüche** (etwas stimmt inhaltlich nicht): z. B. falsches Tool, falsche Modellversion
- **Hörfehler** (nur Schreibweise falsch, Inhalt korrekt): z. B. OpenCla statt OpenClaw

### ⚠️ Doppelt gemeldete Fehler vermeiden

Der Stil-Worker (Worker 2) korrigiert bereits viele Eigennamen. Der Faktencheck-Report sollte vermerken, wenn ein Fehler VOR dem Merge schon offensichtlich war — dann ist die Frage, ob Worker 2 ihn übersehen hat oder ob er erst vom Faktencheck entdeckt wurde.

### ⚠️ Auto-Caption-Zahlen

Auto-Captions von YouTube haben oft seltsame Zahlenfehler:
- `80%` wird zu `80 Prozent` — in Ordnung
- `66708` Views → seltsame Zahl bei frischem Video, plausibel bei 3-4 Monaten Laufzeit
- Datumsangaben werden verwechselt (Upload-Datum im Transkript selten korrekt)

Plausibilitäts-Check: Views/Datum-Relation, Modell-Release-Dates vs. Video-Erscheinungsdatum.

### ⚠️ Description-Kapitelliste kann unvollständig sein („_(weitere)_"-Marker)

YouTube-Descriptions mit nummerierten Listen haben OFT nicht für alle Items explizite Zeitstempel. Typischerweise sind die letzten 1-3 Kapitel nur als „_(weitere)_" markiert oder fehlen ganz. **Das ist KEIN Transkript-Fehler** — der Creator hat sie schlicht nicht getimt.

**Auswirkung auf den Faktencheck:**
- `DESCRIPTION_TIMESTAMPS_VOLLSTAENDIG: nein (N/M)` ist kein Grund für FAIL, nur für WARN
- Die fehlenden Zeitstempel können aus dem Transkript rekonstruiert werden (Kapitelübergänge im Transkript suchen)

**Rekonstruktion aus dem Transkript:** Die letzten nicht-getimten Kapitel finden sich meist über:
1. Die Übergangsphrase des Sprechers („Kommen wir zum letzten Plugin", „Kommen wir zu Nummer X")
2. Den ersten Tool-Namen-Sprech im entsprechenden Transkript-Abschnitt

### ⚠️ Attribution-Fehlt-in-Transkript ≠ Fake

Wenn ein Creator-Name in der Description steht, aber im Transkript nicht vorkommt (z. B. "kepano", "obra", "Upstash"), ist das kein Anzeichen für ein AI-generiertes Transkript oder einen Fake. Der YouTuber hat den Creator-Namen in die Description geschrieben, aber im Voiceover nicht ausgesprochen. Das ist bei Tool-Rankings üblich — der Sprecher sagt "Repository heißt X" anstatt "Repository von Y".

**Handlungsanweisung:** Im Report flaggen, Merger entscheidet über Einfügung in den polierten Text.

### ⚠️ Worker 3 ist der wertvollste Worker im Schwarm (Update 2026-07-09)

Session 2026-07-09 hat empirisch gezeigt: Worker 3 (Faktencheck) hat **14 NEUE Patterns**
identifiziert die Worker 1+2 NICHT kannten (siehe `references/worker3_faktencheck_lessons.md`
für die vollständige Lessons-Datei). Das ist mehr Wert als Worker 1+2 zusammen.

**Konsequenzen für die Königin:**
1. Worker 3 NIEMALS überspringen — er ist die einzige systematische Lücken-Suche
2. Worker 3 Output MUSS in den Merger-Flow integriert werden, nicht nur als "Report"
3. Nach jedem Schwarm: neue Patterns aus Worker 3 in `known-hearing-errors.md` einpflegen

## Siehe auch

- `known-hearing-errors.md` — Such-Matrix mit Regex-Patterns für Post-Merger-Verifikation
- `worker3_faktencheck_lessons.md` — Empirische Erkenntnisse warum Worker 3 der wertvollste Worker ist
- `templates/stufe3_schwarm_delegation_prompts.md` — Copy-pastefertiger Faktencheck-Briefing
- `merger-methodology.md` — Wie Worker 4 die Findings integriert
- `youtube-transcript-saver/SKILL.md` — Stufe 3: Multi-Agent Pipeline-Übersicht
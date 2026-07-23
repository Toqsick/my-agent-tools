---
name: youtube-transcript-saver
description: >-
  Use when user asks for saving a YouTube transcript as Markdown, polishing caption fragments into readable prose, capturing video metadata and timestamps, or archiving transcripts under ~/docs. NOT for downloading video or audio files or creating social posts from a transcript. Builds a clean, source-linked Markdown transcript with metadata, chapters, caption cleanup, and stable filenames.
version: 1.0.0
author: Yuno (für Basti)
lane: media
agent: universal
trigger_keywords: ['youtube', 'transcript', 'save', 'markdown', 'archive', 'caption']
keywords: ['youtube', 'transcript', 'caption', 'video', 'markdown', 'archive', 'metadata']
related_skills: ['youtube-content', 'media-tools', 'transcript-summary', 'youtube-creator']
last_curated: 2026-07-23
curated_by: Yuno (auto-curated v2.1)

license: MIT
platforms:
- linux
- macos
tags:
- media
- youtube
- transcript
- documentation
metadata:
  hermes:
    tags:
    - media
    - youtube
    - transcript
---


# YouTube Transcript Saver

Speichert YouTube-Videos als sauberes Markdown in `~/docs/youtube/` mit:
- YAML-Frontmatter (Video-ID, Metadaten, Tool-Info)
- Header mit Direktlink + Stats
- YouTube-Description + Lernziele + Links
- Vollständiges Auto-Transkript mit Minuten-Markern
- Warnhinweis bei Auto-Generated Captions

## ⚡ User-Präferenzen (Basti, 2026-07-04)

**Delegation-Prompts:** 60-70% der ursprünglichen Länge, Detailgrad behalten aber redundante Erklärungen raus.
**Reasoning:** `high` statt `max` — Agents werden 2-3× schneller.
**Worker-Prompt-Convention:** YAML-Frontmatter im Delegation-Prompt weglassen wo nicht nötig, VERBOTEN-Listen nur 1× statt mehrfach, Status-Report max. 3 Zeilen, keine "Wenn unsicher"-Disclaimer-Ketten.

## Wann diesen Skill nutzen

Trigger: User sagt „transkribier mal", „zieh mir das Transkript", „speicher das Video als Text", oder verweist auf eine YouTube-URL mit Transkript-Wunsch.

Nicht nutzen für: Video-Analyse (→ `video_analyze`), nur Zusammenfassung (→ `youtube-content` Skill), Audio-Extraktion (→ `yt-dlp`/`ffmpeg`).

## Workflow

### 1. Video-ID extrahieren

Aus URL extrahieren — funktioniert für `youtube.com/watch?v=XXX`, `youtu.be/XXX`, oder bare ID:

```bash
# Aus URL: ID ist alles nach v= oder nach youtu.be/
echo "https://www.youtube.com/watch?v=RemmWRiozG0" | grep -oP '(?:v=|/)([A-Za-z0-9_-]{11})' | head -1
```

### 2. Verfügbare Caption-Tracks auflisten

```python
from youtube_transcript_api import YouTubeTranscriptApi
api = YouTubeTranscriptApi()
video_id = "RemmWRiozG0"

try:
    for t in api.list(video_id):
        print(f"{t.language_code} ({t.language}) {'[manuell]' if not t.is_generated else '[auto]'}")
except Exception as e:
    print(f"Fehler: {e}")
```

Bevorzuge manuelle Captions, fallback auf Auto. Wenn mehrere Sprachen: Englisch ist meist genauer als Auto-Deutsch.

### 3. Transkript holen

```python
transcript = api.fetch(video_id, languages=["de"])  # oder ["en", "de"]
# transcript ist Iterable von Snippets mit .start, .duration, .text
```

### 4. Metadaten holen (Titel, Channel, Datum, Stats)

**NICHT yt-dlp nutzen** wenn im Hermes-Venv installiert — cffi-Mismatch zwischen venv (3.11) und System-Python (3.12) macht kaputt. Stattdessen:

```python
from hermes_tools import web_extract
result = web_extract(urls=[f"https://www.youtube.com/watch?v={video_id}"], char_limit=3000)
# Parse Titel/Channel/Upload aus Description-Block
```

Oder via `web_extract` direkt — Title steht in `result["results"][0]["title"]`.

**⚠️ WICHTIG: `web_extract` liefert bei YouTube-Watch-URLs leeren Content!**

YouTube hat aggressive Bot-Protection — `web_extract` bekommt die HTML-Seite, kann aber den JavaScript-rendered Content nicht parsen. Symptom: `result["results"][0]["content"] == ""`. Lösung: **kombinierter Ansatz** (siehe Session 2026-07-09, pvhphecd70Y):

**4a. oEmbed-API für Title + Author (öffentlich, kein Key, immer funktioniert):**

```python
import urllib.request, json
oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
with urllib.request.urlopen(oembed_url, timeout=10) as resp:
    meta = json.loads(resp.read())
# meta["title"], meta["author_name"], meta["author_url"], meta["thumbnail_url"]
```

**4b. curl mit User-Agent-Header für Description + Timestamps + Views:**

```bash
curl -s -L -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36" \
  "https://www.youtube.com/watch?v=${VIDEO_ID}" -o /tmp/yt_page.html

# Description-Block extrahieren:
grep -oE '"description":\{"simpleText":"[^"]{50,3000}"' /tmp/yt_page.html | head -1

# Upload-Date + View-Count + Like-Count:
grep -oE '"uploadDate":"[^"]+"' /tmp/yt_page.html | head -1
grep -oE '"viewCount":"[0-9]+"' /tmp/yt_page.html | head -1
grep -oE '"likeCount":"[0-9]+"' /tmp/yt_page.html | head -1

# Timestamps aus Description:
grep -oE '\d{1,2}:\d{2}\s+[A-Z][^\\"]{5,80}' /tmp/yt_page.html | head -15
```

`simpleText` Description kann Newlines als `\n` enthalten — bei der Markdown-Ausgabe zu echten Newlines konvertieren. View/Upload-Date sind in der HTML als JSON-encoded Strings drin, direkt parsbar.

**4c. yt-dlp-Fallback (nur wenn 4a+4b scheitern):** Siehe Pitfall-Block unten — funktioniert im Hermes-Default NICHT wegen cffi-Mismatch. Alternative: `yt-dlp` aus System-Python mit `--user-agent` benutzen statt aus Hermes-Venv.

### 5. Caption-Polishing (sehr empfohlen)

Auto-Captions kommen zeilenweise kaputt raus — Mid-Wort-Bruchstücke („OpenCla\\nirgendwie"), Zeilensprünge mitten im Satz, fehlende Satzzeichen, holprige Grammatik. **Vor dem Markdown-Bau** polishen, sonst sieht's aus wie Rohmüll.

**Prinzip:** Erst alle Snippets zu einem einzigen Textblob zusammenkleben, dann mit deterministischen Regex-Fixes + LLM-Pass glätten.

**5a. Snippets zusammenfügen (statt zeilenweise):**

```python
# Roh: jedes Snippet ist eine separate Zeile, oft mit Wortbrüchen
# Beispiel-Roh-Snippets:
#   "Hast du das Gefühl, dass dein OpenCla"
#   "irgendwie nicht so gut funktioniert, wie"
#   "es alle immer sagen?"

texts = [entry.text.replace("\n", " ").strip() for entry in transcript]
blob = " ".join(texts)

# Erste Sanitisierung (deterministisch, kein LLM nötig):
import re
blob = re.sub(r"\s+", " ", blob)                    # Mehrfach-Whitespace normalisieren
blob = re.sub(r"\s*-\s+", "", blob)                 # Binde-Striche mit Spaces zusammenfügen
# Achtung: KEIN blindes Lowercase-Merge zwischen Wortgrenzen, sonst
# werden echte Bindestrich-Wörter wie "Open-Source" zu "OpenSource".
```

**Polishing-Skript zum Copy-Pasten (deterministischer Pre-Pass):**

```python
import re
from pathlib import Path

def polish_caption(raw_text: str) -> str:
    """Deterministischer Caption-Pre-Polisher (kein LLM, schnell)."""
    t = raw_text
    t = re.sub(r"\s+", " ", t)                                    # Whitespace normalisieren
    t = re.sub(r"\s*-\s+", "-", t)                                # Soft-Hyphen-Brüche schließen
    t = re.sub(r"\s+([.,!?;:])", r"\1", t)                        # Space vor Satzzeichen weg
    t = re.sub(r"([.,!?;:])([a-zäöüß])", r"\1 \2", t)             # Space NACH Satzzeichen
    t = re.sub(r"\.\s*\.\s*\.", "...", t)                         # „..." normalisieren
    t = re.sub(r"\b10 mal\b", "10-mal", t)                        # „10 mal" → „10-mal"
    return t

# Anwendung:
raw = Path("/tmp/transcript_RemmWRiozG0.md").read_text()
polished = polish_caption(raw)
```

**5b. LLM-Pass: Sätze glätten + Eigenname-Korrektur (3 Stufen)**

Der LLM-Pass ist **optional und eskaliert in 4 Stufen** (0-3). Default für Basti: **Stufe 0** (= nichts, nur deterministisch). Nur bei explizitem „lesbar" / „geglättet" hochstufen.

**Stufe 0 — Deterministischer Pre-Pass (siehe 5a, keine LLM-Kosten)**

**Stufe 1 — Schneller Inline-Polish (aktuelles Modell, kleines Kontextfenster)**

Funktioniert NUR, wenn das LLM einen direkten Text-Input akzeptiert. In Hermes macht das `delegate_task` mit `goal` und einem kleinen Inline-Worker-Subagenten — billig und schnell:

```python
from delegate_task import delegate_task

result = delegate_task(
    goal=f"""Du bist ein Transkript-Polisher. Gegebener Text ist eine 
YouTube-Auto-Caption (Deutsch). 

DEINE AUFGABEN (streng, nichts anderes):
1. Setze korrekte Satzzeichen (Punkte, Kommas, Fragezeichen)
2. Repariere Wortbrüche wie 'OpenCla irgendwie' → 'OpenClaw irgendwie'
   oder besser den echten Eigennamen wenn erkennbar
3. Glätte offensichtliche Auto-Caption-Hörfehler (QdRANT→Qdrant, 10 mal→10-mal)
4. Behalte den Sprachstil (umgangssprachlich OK)
5. Strukturiere in Absätze an Sinnpausen — aber NICHT inhaltlich verändern

VERBOTEN:
- KEINE Zusammenfassung, kein Weglassen, keine neuen Infos
- KEINE Halluzinationen oder 'Verbesserungen'
- KEINE Füllwort-Eliminierung ('ähm', 'halt', 'quasi' gehören zum Stil)

Wenn unsicher: im Original belassen.

Gib NUR den polierten Text zurück, ohne Vor- oder Nachgeplauder.

ORIGINAL-TEXT:
{blob[:3000]}""",
    context=f"Video-ID: {video_id}, Sprache: {lang}, Caption-Type: {'auto' if is_generated else 'manual'}",
)
polished = result.output
```

**Stufe 2 — Subagent-Worker mit Prompt-File (für >3000 Wort Blobs)**

Bei langen Captions (>3000 Token) reicht der Inline-Prompt nicht mehr. Dann Subagent mit Prompt-File und Write-Access — Worker schreibt direkt in die Markdown-Datei:

```python
from delegate_task import delegate_task

# Prompt-Template schreiben
prompt_path = Path("/tmp/polish_prompt.txt")
prompt_path.write_text(f"""Du bist Transkript-Polisher. Lies {raw_md_path} 
(Input: rohes Caption-Markdown). 

Aufgaben: (siehe oben Stufe 1).

Schreibe das Ergebnis nach {output_md_path}. Header und Frontmatter 
bleiben unverändert — nur die Sektion '## 📝 Transkript' wird ersetzt.
Original-Blob bleibt im Hidden-HTML-Comment am Dateiende.
Wortzahl-Drift >5% = Fehler, dann abbrechen und melden.
""")

result = delegate_task(
    goal=prompt_path.read_text(),
    context=f"Video-ID: {video_id}, Sprache: {lang}, Ziel-Datei: {output_md_path}",
    role="leaf",
)
```

**Stufe 3 — Multi-Agent (3 Worker parallel: Inhalt / Stil / Faktencheck + Merger)**

Für **wichtige / zitierfähige Transcripts**: drei Subagenten parallel starten, dann Merger:
- **Inhalt-Worker**: poliert rein sprachlich (Satzzeichen, Wortbrüche, Absatz-Struktur)
- **Stil-Worker**: korrigiert Eigennamen + Tech-Begriffe (anhand Video-Description-Kontext), gibt Liste der gefixten Begriffe zurück. Siehe `references/worker2-stil-methodology.md` für die vollständige Worker-2-Methodik (Ordered-Regex-Ansatz, longest-patterns-first, Output-Wrapper-Convention, UNSICHER-Dokumentation). **Swarm-Variante:** In Multi-Worker-Setups mit `/tmp/yt_remote_workers/`-Layout bekommt Worker 2 eine explizite `context.md` mit Heuristik-Liste statt Description-Scan, und einen worker-spezifischen Output-Wrapper `===START_WORKER2_STIL===` mit zwingendem Status-Block (Wortzahl, Drift, Marker-Count, `Claudee`-Assertion). Details zu Pass-Ordering-Falle (Compound vs. Standalone), case-insensitive Matching für Auto-Caption-Mangles, und Cross-Check gegen `input_raw_caption.txt` siehe `references/worker2-stil-methodology.md` → Inputs / Pass-Ordering-Falle / Case-Insensitive Matching / `Claudee`-Assertion.
- **Faktencheck-Worker** (⭐ **besonders wertvoll**): vergleicht polierten Output mit Description-Aussagen + Zeitstempeln, meldet Widersprüche. Liefert zusätzliche Hörfehler die Worker 1+2 übersehen haben. Siehe `references/faktencheck-methodology.md` für die vollständige Worker-3-Methodik (grep-basierte Keyword-Suche, Description-Tag-Cross-Reference, Report-Struktur, Pitfalls bei Single-Line-Transkripten).

Dann ein 4. **Merger-Worker** der die drei Outputs zusammenführt. Aufwand: 4× LLM-Calls.

**Stufe 4 — LLM-Glättung (Single-Worker, nach Stufe 3) [NEU, Session 2026-07-09]**

Für **zitierfähige Transcripts** (Schulungs-Material, Reference-Docs, Blog-Beiträge) — sprachliche Politur NACH der Stufe-3-Pipeline. Stufe 4 ist **polishing-only**: keine inhaltlichen Änderungen, keine Eigenname-Fixes (Stufe 3 erledigt), nur sprachliche Verfeinerung.

**Wann Stufe 4 einsetzen:**
- ✅ Für Reference-Material das zitiert wird (z.B. Julian-Reihe die als Lern-Basis dient)
- ✅ Wenn Lesbarkeit wichtiger ist als Schnelligkeit
- ❌ NICHT für Quick-Save-Captures (Stufe 3 reicht)
- ❌ NICHT für Transcripts mit unklarem Inhalt (Stufe 4 würde halluzinieren)

**Sub-Phasen (KÖNIGIN orchestriert, NICHT der Worker):**

**Sub-Phase 4.1 — Hochsichere Ambiguitäten deterministisch fixen (VOR dem LLM!)**

Der LLM wird jede Ambiguität als "Fehler" erkennen und eine "Lösung" halluzinieren. Deshalb MUSS die Königin vorher die Fälle fixen, die sie mit hoher Sicherheit auflösen kann:
- Video-Kontext prüfen (z.B. "KFM2 Plan" + "Hostinger" im Description → KVM 2 mit 85% Sicherheit)
- External Knowledge nutzen (z.B. "Resent versendet Emails" → Resend-API mit 90% Sicherheit)
- Nur Fixes mit ≥80% Sicherheit anwenden, restliche Ambiguitäten dokumentieren
- Diese Fixes zählen NICHT als Stufe-4-Korrekturen sondern als Pre-Phase

**Confidence-Schwellen für Ambiguitäts-Fixes (gemessene Daten aus Session 2026-07-09):**

| Confidence | Aktion | Beispiele |
|------------|--------|-----------|
| **≥90%** | Königin fixt deterministisch | `Resent` → `Resend` (E-Mail-API ist etabliert, https://resend.com) |
| **80-89%** | Königin fixt deterministisch + dokumentiert im Header | `KFM2` → `KVM 2` (Hostinger-Standardtarif, Beschreibung enthält Hostinger-Kontext) |
| **50-79%** | Belassen + im Header dokumentieren als Verdacht | `[musik]` → "Auto-Mode-Setting" (Kontext unklar, könnte auch UI-Element sein) |
| **<50%** | Belassen + im Header dokumentieren ohne Verdacht | `Textag` (unklar ob "Text" oder "Textvorschlag" oder anderes) |

**Faustregel:** Bei 80-89% Confidence darf die Königin fixen, MUSS aber den Fix im Header als "gefixt mit X% Sicherheit" markieren. Bei ≥90% reicht eine kurze Notiz. Bei <80% NIE fixen — lieber Worker 5 die Ambiguität konservativ behandeln lassen (er hat die Anweisung sie NICHT anzufassen).

**Warum die Schwelle wichtig ist:** Wenn die Königin eine Ambiguität mit 60% Confidence fixt und falsch liegt, ist das ein **vom Menschen verursachter Fact-Fehler** im polierten File — schlimmer als wenn die Ambiguität unklar bleibt. Der User kann eine dokumentierte Unklarheit selbst recherchieren; ein falscher "Fix" sieht aus wie ein Fakt.

**Sub-Phase 4.2 — Worker 5 (LLM-Glättung) dispatchen**

Single-Worker-Subagent (`role='leaf'`) mit Output nach `/tmp/yt_llm_worker/output_worker5_llm.md`. Strikt-Constraints im Briefing:
- KEINE Eigenname-Fixes (Stufe 3 erledigt — siehe Context-Liste)
- KEINE inhaltlichen Änderungen
- KEINE Füllwort-Reduktionen (Creator-Stil erhalten — `halt`, `quasi`, `natürlich`, `eigentlich`, `irgendwie`, `mega cool`, `ne` sind Sprachstil, nicht eliminieren)
- ±2% Drift-Limit (enger als Stufe 3 weil LLM-Polish nur kosmetisch)
- 2 Rest-Ambiguitäten NICHT anfassen (im Header dokumentiert)

Erwartete Worker-5-Fixes:
- 30-50 Satzzeichen-Korrekturen (Kommas vor Nebensätzen, Punkte am Satzende, Relativpronomen-Deklination)
- 0-10 Wort-Reparaturen (Komposita, Rechtschreibung dass/das, fehlende Substantive)
- 0 Füllwort-Reduktionen (wenn die Constraints respektiert werden)

**Gemessene Worker-5-Reparatur-Beispiele aus Session 2026-07-09 (pvhphecd70Y) — alle ECHTE Grammatik-Fixes, keine Halluzinationen:**

| Input (Stufe-3) | Output (Stufe-4) | Warum korrekt |
|------------------|------------------|---------------|
| `mit dem wir Claude dazu bringen` | `mit denen wir Claude dazu bringen` | Relativpronomen-Deklination: Bezug auf "Befehle" (Plural) |
| `Danke, Seite und Bestätigungsmail` | `Danke-Seite und Bestätigungsmail` | Kompositum statt Komma — Thank-You-Page ist ein Begriff |
| `dass ich plane` | `das ich plane` | Rechtschreibung: "dass" ist Konjunktion, "das" wäre Relativpronomen — Kontext ist Konjunktion |
| `erstellst für mein Webinar` | `erstellst für mein Webinar, das ich plane` | Fehlendes Substantiv ("Website") aus Kontext ergänzt |

**Lesson für die Königin:** Worker-5-Wort-Reparaturen SIND in der Regel echte Grammatik-Fixes, keine Halluzinationen — auch wenn sie wie "Veränderungen" aussehen. Die Constraints "Julians Stil erhalten" + "Eigennamen nicht anfassen" + "Rest-Ambiguitäten nicht anfassen" schützen vor den schlimmsten Halluzinationen. Bei Verdacht: Original-Caption aus `<!-- RAW_CAPTION_BLOB -->` greppen und Julian's Aussprache checken.

**Anti-Pattern: Königin darf Worker-5-Wort-Reparaturen NICHT blind rückgängig machen** weil sie "Veränderungen" sind. Die Verifikation muss sein:
1. Ist die Reparatur grammatikalisch korrekt? (Relativpronomen-Deklination, Rechtschreibung)
2. Ist die Reparatur kontextuell konsistent? (Kompositum-Bildung wenn Substantiv-Verbindung gemeint)
3. Ist die Reparatur im Original-Ton? (NICHT eliminieren wenn sie Julians Sprachstil entspricht)

Wenn 1+2+3 alle TRUE → Reparatur behalten. Nur bei eindeutiger Halluzination (z.B. Worker erfindet Substantiv das nicht im Kontext steht) rückgängig machen.

**Sub-Phase 4.3 — Wall-Clock 30-60s**

LLM-Pass ist Single-Pass (kein Merger nötig bei guter Disziplin). Polling-Loop alle 10s, max 6 Min Timeout.

**Sub-Phase 4.4 — Integration + Header-Update**

Worker-5-Transkript in Original-Markdown einbauen, Header von "Stufe 3" auf "Stufe 4" updaten, Rest-Ambiguitäten-Liste aktualisieren (2/4 gefixt, 2/4 bleiben).

**Sub-Phase 4.5 — Verifikation**

Wortzahl-Drift, Restfehler-Check, Eigennamen-Counts müssen UNVERÄNDERT sein (Stufe 3 hat das festgelegt).

**Gemessene Performance (Session 2026-07-09, pvhphecd70Y, Stufe 4):**
- Laufzeit: ~50 Sekunden (Worker 5 single-pass, viel schneller als Stufe 3)
- Wort-Drift: -0.06% (4904 → 4901, weit unter ±2%)
- Minuten-Marker: 23/23 erhalten
- 38 Satzzeichen-Korrekturen + 4 Wort-Reparaturen + 0 Füllwort-Reduktionen
- Post-Stufe-4-Restfehler: 0 (null)
- Wall-Clock gesamt: ~5 Min (2 Min deterministische Fixes + 50s LLM + 3 Min Integration)

**Gemessene Performance (Session 2026-03-15, Claude Code 8 Best Practices, ~5500 Wörter):**
- Laufzeit: ~260 Sekunden (3 parallel + 1 sequentiell)
- Wort-Drift: -1,27% (5588 → 5520) — weit unter 5%-Limit
- Minuten-Marker: 27/27 erhalten
- ~169 Hörfehler korrigiert (Stil + Faktencheck kombiniert)
- Post-Merger-Restfehler: 2× Compound-Word-Varianten (MCPS Server → MCP-Server)

**Zusätzlicher Data Point (Session 2026-07-04, 5 OpenClaw Usecases, ~4900 Wörter, 23 Minuten-Marker):**
- Merger-Laufzeit: ~4 Minuten (etwas länger durch detaillierteren Faktencheck-Report mit 27 zusätzlichen Hörfehlern)
- Wort-Drift: -1,6% (4943 → 4862) — signifikant besser als 5%-Limit
- Minuten-Marker: 23/23 erhalten
- ~50+ Eigenname-Fixes (21× OpenCla→OpenClaw, plus 30+ weitere Korrekturen)
- Post-Merger-Restfehler: 0 (null) — null verbleibende Hörfehler im polierten Bereich
- Faktencheck-Warnungen: Description-Tag-Diskrepanzen (Telegram nur als CLI-Befehl, VPS/Clawdbot/Moltbot nicht wörtlich im Transkript)

**Neuester Data Point (Session 2026-07-04, NVUCQ-pzBn4, Obsidian+Claude-Code-Setup, 36:24, 7.374 Wörter):**
- Merger-Laufzeit: ~4 Minuten
- Wort-Drift: +0.7% (7.374 → 7.426, inklusive Marker-Text)
- Minuten-Marker: 37/37 erhalten
- ~105 Eigennamen-Fixes (Cloud→Claude 32, Cloud Code/Cowork 24, CLAUDE.md 8, WT/VT/Volt→Vault 13, Markdown-Fixes 5, plus weitere)
- Post-Merger-Restfehler: 0 (null) — beste Quality-Bilanz eines nicht-Julian-Ivanov-Runs
- Besonderheit: Erster Run mit Obsidian-spezifischen Hörfehlern (Obsidien, Kontextordr, Mark-Dateien, Brain-Dump-Komposita)
- Siehe `references/merger-methodology.md` für die vollständige Merger-Methodik und Post-Merge-Verifikation.

**Worker-Output-Convention (wichtig für Merger-Zuverlässigkeit):**
Jeder Worker schreibt sein Ergebnis in eine separate Datei (`/tmp/yt_polish_output_<worker>.md`) mit Markern:
```text
===START_<WORKER>===
<poliert>
===END_<WORKER>===
```
UND hängt einen **Status-Block** ans Datei-Ende:
```text
===STATUS_<WORKER>===
Wörter: NNNN
Gefixt: Begriff_A (Nx), Begriff_B (Mx)
Minuten-Marker: N/Total
Wort-Drift: +/-X%
```
Nicht nur auf stdout — sonst hat der Merger keinen Referenzpunkt.

**Worker 1 (Inhalt) — Detaillierte Spezifikation:** Siehe `references/worker1-inhalt-methodology.md` für die vollständige Methodik (Aufgaben, Verbote, Minuten-Marker-Verteilung, Self-Verification, Output-Wrapper-Format und Pitfalls). Enthält ergänzte Praxis-Daten aus einem 42:48/8.758-Wörter-Transkript-Lauf (Session 2026-07-04).

**Merger-Pitfalls (aus der Praxis):**
- **Compound-Word-Varianten**: Ein Fix für `MCP` erwischt nicht automatisch `MCPS`, `MCPS-Server`, `MCP-Server`. Der Merger braucht eine erweiterte Muster-Liste inklusive Flexionen.
- **Falsch-positive erkennen**: `OpenClaw` (Eigenname eines Tools) ≠ `OpenClaw`-Fehler. Der Merger muss die Fix-Liste aus Worker 2 gegen die Heuristik-Liste (5c) checken, nicht blind ersetzen.
- **Nicht gefixt == gelöscht**: Wenn ein Worker einen Begriff nicht korrigiert hat, checken ob (a) es kein Fehler war oder (b) ein echter Fehler übersehen wurde.
- **Cloud-Code vs Claude Code Disambiguierung (Compound-Adjective-Kontext)**: Nicht jedes "Cloud Code" im Caption-Blob meint "Claude Code". Compound-Adjektive wie "Cloud-Code-Skill" (ein von Claude Code erstellter Skill) bleiben als "Cloud-Code-Skill" erhalten — hier ist "Cloud-Code" ein deskriptives Compound-Adjektiv, kein falscher Eigenname. Der Merger muss unterscheiden zwischen: (a) Standalone "Cloud Code" → "Claude Code" (Korrektur), (b) "Cloud-Code" als Compound-Adjektiv im Bindestrichwort → belassen (kein Hörfehler). Faustregel: Wenn "Cloud Code" Teil eines Compound-Worts mit Bindestrich ist → belassen. Sonst → ersetzen.

**Post-Merger-Verifikation (zwingender Folgeschritt — ZWEI Pässe):**
Nach dem Merge gezielt nach Restfehlern suchen — vor allem Compound-Word-Varianten die der Merger übersehen hat. Die erweiterte Heuristik-Liste in `references/known-hearing-errors.md` enthält eine vollständige Such-Matrix.

**Wann welche Stufe?**

| Stufe | Aufwand | Wann | LLM-Calls |
|-------|---------|------|-----------|
| 0 (nur Regex) | <1 Sek | Kurze Clips, Quick-Save | 0 |
| 1 (Inline-Delegate) | ~30 Sek | Mittlere Videos, Basti will's lesen können | 1 |
| 2 (Worker mit Files) | ~1-2 Min | Lange Videos (>15 Min), finale Save-Quality | 1 |
| 3 (Multi-Agent) | ~3-5 Min | Zitierfähige Transcripts, Reference-Material | 4 |
| 4 (LLM-Glättung nach Stufe 3) | ~5 Min (2 Min Königin-Fixes + 50s LLM + 3 Min Integration) | Schulungs-Material, Blog-Beiträge, Reference-Docs | 1 |

**Default für Basti:** Stufe 0. Hochstufen nur bei explizitem Wunsch oder wenn die Datei später als Referenz dienen soll.

**5c. Heuristik-Liste für bekannte Wortverhunzer**

| Auto-Caption schreibt | Eigentlich | Kontext-Hinweis |
|----------------------|-----------|----------------|
| `OpenCla` (ohne w) | **Kontextabhängig:** `OpenClaw` (Julian Ivanov) oder Tool-Name (generisch) | Julian zählt OpenClaw als sein eigenes Tool in der Trinität Claude Code/Codex/OpenClaw/Hermes. **NIE** automatisch zu OpenCode auflösen — erst Channel prüfen! |
| `QdRANT`, `Quadrant` | `Qdrant` | Vector Database |
| `10 mal` | `10-mal` oder `10×` | 10 mal stärker |
| `n8n` | `n8n` | meist korrekt |
| `Make.com` | `Make.com` | meist korrekt |

**Speziell für KI-Coding-Tutorials (häufigste Fehler):**

| Auto-Caption | Korrekt | Erklärung |
|-------------|---------|-----------|
| `Cloud Code`, `Clot`, `Cloud` (eigenständig, als Agent) | `Claude Code` / `Claude` | Anthropics Coding-Agent — häufigster Fehler. **90× eigenständiges `Cloud`→`Claude`** in einem Run (V6, 42:30 Compilation). ASR erkennt `Cloud` wo der Sprecher `Claude` meint — fast immer wenn Claude als Actor/Agent im Satz steht. |
| `Cloud MDatei`, `Cloud MDien`, `Cloud MDI`, `Cloud MDEI`, `Cloudmdatei` | `CLAUDE.md` | Projekt-Konfigurationsdatei |
| `Cloud Instanz` | `Claude-Instanz` | Die laufende Claude-Instanz |
| `Superagent`, `Supagent`, `SuperAgent` | `Subagent` | Claude Code Sub-Agent-Pattern |
| `Hauptgagent` | `Hauptagent` | Der primäre Agent im Chat |
| `Anthopic` | `Anthropic` | Company Name |
| `Antiravity` | `Antigravity` | Andere Coding-Agent-Plattform |
| `Highq`, `HighQ` | `Haiku` | Claude-Modell (Haiku) |
| `Son`, `Sonell` (einzelnstehend) | `Sonnet` | Claude-Modell (Sonnet) |
| `Quen Code` | `Qwen Code` | Alibaba Coding-Agent |
| `Excalid Draw`, `Excaly Draw` | `Excalidraw` | Diagramm-Tool |
| `Yammel Front Met` | `YAML Frontmatter` | YAML-Header in Skills/Markdown |
| `Kontext Rod` | `Context Rot` | Degradation bei vollem Kontext |
| `Areal ` (Schriftart) | `Arial ` | Schriftart-Name |
| `Thorally` | `Thoroughly` | gruendlich im Englischen |
| `MCPS`, `MCPS-Server`, `MCPS Server` | `MCP`, `MCP-Server` | Model Context Protocol |
| `SLGal`, `SLRemote`, `slem Control` | `/goal`, `/remote Control` | Slash-Command-Verhunzungen (Session 2026-07-09) |
| `SlashLOP`, `Slashloop`, `SlashG` | `/loop`, `/goal` | Slash-Command-Verhunzungen (Session 2026-07-09) |
| `Tmax`, `TMAX`, `T-Max` | `tmux` | Terminal-Multiplexer, Julian Remote-Control-Video |
| `Hey Claud`, `Hey Clud`, `Clode`, `Clot` | `Hey Claude`, `Claude` | Eigenname-Anrede verhunzt (Session 2026-07-09) |
| `Rustinger` | `Hostinger` | VPS-Anbieter-Verhunzung (Session 2026-07-09) |
| `closed starten` | `claude starten` | Kommandozeile (Session 2026-07-09) |
| `JGPT` | `ChatGPT` | OpenAI |
| `SLCCtext` | `/compact` | Claude Code Slash-Command |
| `@AGs` | `/AGs` | Claude Code Slash-Command |
| `CL` | `Claude` | Abkuerzung im Fliesstext |
| `Use Casases` | `Use Cases` | Englischer Plural |
| `Loginystem` | `Login-System` | Zusammenschreibung |

Siehe auch `references/known-hearing-errors.md` fuer eine durchsuchbare Such-Matrix inklusive Regex-Patterns fuer die Post-Merger-Verifikation.

**5d. Im Header flaggen wenn poliert:**

```markdown
> ⚠️ **Hinweis:** Auto-generated · geglättet von Yuno (Satzzeichen, 
> Wortbrüche repariert, ~3% Eigenname-Korrekturen)
```

**5e. Original-Blob optional mitspeichern**

Falls User später selbst nachpolieren will — pack den Roh-Blob als versteckten Block ans Dateiende:

```markdown
<!-- RAW_CAPTION_BLOB (ungeglättet, ~8500 Wörter)
<blob hier>
-->
```

### 6. Markdown-Datei bauen

**Filename-Schema:** `~/docs/youtube/YYYY-MM-DD_<slug>_<VIDEOID>.md`

```python
slug = "openclaw-10x-staerker"  # aus Titel, lowercased, ASCII, hyphens
filename = f"{upload_date}_{slug}_{video_id}.md"
```

**Aufbau (in dieser Reihenfolge):**

```markdown
---
source: https://www.youtube.com/watch?v=VIDEOID
title: "Originaler YouTube-Titel"
channel: "Channel-Name"
uploaded: YYYY-MM-DD
duration: HH:MM
views: NNNN
likes: NNNN
language: Deutsch (auto-generated)  # oder Englisch (manuell) etc.
captured: YYYY-MM-DD
tool: youtube-transcript-api (Python 3.12)
---

# <Titel>

> 📺 Quelle: [youtube.com/watch?v=VIDEOID](URL)  
> 🎙️ Kanal: Channel · 👁️ N Views · 👍 N Likes · 🗓️ Datum

## Kurzbeschreibung (aus Video-Description)

<Description-Text>

### Lernziele / Was im Video vorkommt (aus Description)

- Bullet-Points aus den "Was du lernst"-Sektionen

### Weiterführende Links

- Affiliated URLs (Skool, Tools, etc.)

### Zeitstempel (aus Video)

- `00:00` Kapitel 1
- `02:14` Kapitel 2

---

## 📝 Transkript

> ⚠️ **Hinweis:** Auto-generated / manuell erstellt von YouTube / von Yuno übersetzt etc.

## [00:00]

<Text aus erstem Segment>

## [00:01]

<Text aus Segmenten mit start in dieser Minute>
```

### 6a. Minuten-Marker richtig setzen

Pro Segment mit `start` in Sekunden:

```python
current_minute = -1
for entry in transcript:
    minute = int(entry.start // 60)
    second = int(entry.start % 60)
    if minute != current_minute:
        print(f"\n## [{minute:02d}:{second:02d}]\n")
        current_minute = minute
    print(entry.text.replace("\n", " ").strip())
```

### 7. Speichern + Verifizieren

```bash
mkdir -p ~/docs/youtube/
# Datei schreiben
ls -la ~/docs/youtube/2026-03-02_<slug>_<VIDEOID>.md
wc -w ~/docs/youtube/*.md  # Wortzahl plausibel? (>1000 für 30+ Min Video)
```

## Pitfalls

### ⚠️ yt-dlp ist im Hermes-Default kaputt

**Symptom:**
```
Exception: Version mismatch: this is the 'cffi' package version 2.0.0, located in
'/home/bratan/.hermes/hermes-agent/venv/lib/python3.11/site-packages/cffi/api.py'.
When we import the top-level '_cffi_backend' extension module, we get version 1.16.0,
located in '/usr/lib/python3/dist-packages/_cffi_backend.cpython-312-x86_64-linux-gnu.so'.
```

**Ursache:** Hermes-Venv nutzt Python 3.11, System-Python ist 3.12, `cffi` Pakete mismatchen.

**Lösung:** `yt-dlp` einfach nicht nutzen für Transcripts. Direkt `youtube-transcript-api` mit `python3.12` aufrufen — das umgeht das Problem komplett.

Falls doch mal nötig: `pip install --user --upgrade cffi` in der Hermes-Venv ODER yt-dlp im System-Python mit eigener Venv isolieren.

### ⚠️ Auto-Captions sind teils Wortverfälscht

YouTube-Auto-Captions verhunzen oft Eigennamen. Beispiel aus echtem Run:
- **OpenCla** (ohne w) → **kontextabhängig** (bei Julian Ivanov: OpenClaw, generisch: Tool-Name)
- **„QdRANT"** statt **„Qdrant"**
- **„Skript"** statt **„Script"**

**Im Header notieren**, dass es Auto-Generated ist. Der **Polishing-Step (5)** ist genau dafür da — entweder deterministisch (Regex) oder per LLM-Pass mit explizitem Korrektur-Prompt.

**Faustregel:** Nie inhaltlich raten. Wenn Wort unklar → im Original belassen und im Header markieren.

### ⚠️ LLM-Polishing-Pass kann Inhalt verlieren

Wenn du den Caption-Text durchs LLM schickst, **passiert schnell**:
- Zusammenfassen statt glätten (Output ist halb so lang wie Original)
- Halluzinierte „Verbesserungen" (Sätze umformuliert, Infos erfunden)
- „Aufräumen" von Füllwörtern wie „ähm", „halt", „quasi" — die aber oft Charakter haben

**Gegenmaßnahmen:**
- Prompt **explizit** sagen lassen: „KEINE Zusammenfassung, keine Auslassungen, kein Hinzufügen"
- Output-Länge mit Original-Wortzahl vergleichen (sollte ~95-105% sein)
- Bei sensiblen Inhalten: nur deterministischen Pre-Pass (5a) machen, kein LLM
- Original-Blob immer mitspeichern (Schritt 5e) — falls Polishing Mist baut, Rohmaterial ist da

### ⚠️ Manche Videos haben nur 1 Caption-Track

Kein manueller, kein englisches Original — nur z.B. Deutsch auto-generated. Dann halt das nehmen, klar im Header markieren, fertig.

Wenn gar nichts da ist: `TranscriptsDisabled` Exception → User informieren, ggf. `video_analyze` als Multimodal-Fallback vorschlagen.

### ⚠️ Lange Videos → lange Markdown-Files

38-Minuten-Video = ~8.500 Wörter = 50 KB Markdown. Inline in Chat anzeigen ist Anti-Pattern — immer als Datei speichern und nur Zusammenfassung + Pfad zurückgeben.

### ⚠️ Description-Parsing

Nicht die YouTube-Webseite voll scrapen — nur Description-Block reicht. `web_extract` mit `char_limit=3000` ist sweet spot.

### ⚠️ After-Delivery Worker Outputs — zweiter Verifikations-Pass nötig

Bei Stufe 3 (Multi-Agent) können Worker-Outputs **3-30 Minuten nach dem Merge** eintrudeln. `delegate_task` ist asynchron: der Merger startet sobald alle 3 Worker ihre erste Antwort liefern, aber einzelne Worker können durch Retry/Delay eine zweite, bessere Antwort 3-30+ Minuten später abliefern.

**Timing-Muster aus der Praxis (Session 2026-07-04, V6 42:30 Compilation):**
- Inhalt-Worker: nach ~82s (erste Version)
- Stil-Worker: nach ~223s (finale Version mit 184 Fixes)
- Faktencheck-Worker: nach ~89s (zweiter Output mit 22 zusätzlichen Findings nach ~3,7 Min)
- **Nachgelieferte Korrekturen**: 3x `OpenCla`→`OpenClaw` erst durch spätere Worker-Delivery erkannt

**Verhalten:**
1. Merge auf Basis der ERSTEN (schnellsten) Worker-Outputs
2. File zusammenbauen und speichern
3. **WENIGSTENS 5 Min warten**, ob weitere Worker-Outputs eintrudeln (sichtbar als `[ASYNC DELEGATION BATCH COMPLETE]` im Chat)
4. **Zweiten Verifikations-Pass** laufen lassen: Restfehler-Check mit `post_merge_verification()` gegen den FINALEN (bereits gebauten) File
5. Nachbesserungen als separate Patches auf den bestehenden File anwenden

### ⚠️ Marker-Count mit grep verfälscht

Beim Zählen der Minuten-Marker mit `grep -c "^## [0"` werden nur Marker von `[00:xx]` bis `[09:xx]` gezählt — Marker ab Minute 10 (`## [10:00]` etc.) werden übersehen. Ergebnis z. B. 10 statt 27 Marker (false-negative).

**Korrekt:** `grep -c '^## \['` — ohne Einschränkung auf `[0`.

Dieser Fehler passiert schnell bei der Verifikation nach dem Merge, weil man intuitiv `[0` als "Anfang des Timestamps" assoziiert. Immer den vollständigen Regex `'^## \['` nutzen.

### ⚠️ Briefing-Disziplin: Königin muss Annahmen VERIFIZIEREN bevor sie Worker-Briefings schreibt [NEU, Session 2026-07-09]

**Erkenntnis:** Wenn die Königin in einem Worker-Briefing einen "Bug" beschreibt, den ein anderer Worker angeblich eingeführt hat, MUSS sie das vorher verifiziert haben. Sonst reproduziert die Worker-Biene die Halluzination.

**Konkretes Beispiel (Session 2026-07-09, pvhphecd70Y Stufe 3):**
- Königin las die ersten 50 Zeilen von Worker 2's Output und sah "Claudee Code" → schloss "Worker 2 hat Bug eingeführt"
- Tatsächlich: Worker 2's **Final-File** hatte 0× Claudee (Worker 2 hatte den selbst-erzeugten Bug in eigener zweiter Iteration eliminiert)
- Königin gab Merger-Biene Briefing "Claudee-Bug fixen" — die Merger-Biene hat richtig hinterfragt und korrekt nichts geändert
- **Glück im Unglück**: Die Biene war diszipliniert genug, das Briefing zu hinterfragen

**Faustregel für Königinnen-Briefings:**

Schlecht (verifiziert nicht, kann Halluzinationen auslösen):
```
Worker 2 hat "Cloud" zu aggressiv zu "Claudee" gemacht! DAS IST EIN BUG.
Korrigiere ueberall "Claudee" zu "Claude".
```

Gut (verifiziert, klare Aktion):
```
Falls du Claudee im Worker-2-Output findest (grep -c 'Claudee' Worker2_File),
korrigiere zu Claude. Wenn 0 Vorkommen: kein Fix nötig, im Status dokumentieren.
```

**Faustregel für alle Worker-Bienen (in allen Stufen):**
- Bei Briefing-Annahmen die ungeprüft sind: selbst verifizieren (`grep -c`, `find`, `wc -w`)
- Wenn der angebliche Bug nicht existiert: transparent kommunizieren statt ihn zu "fixen"
- Die Anweisung "Wenn unsicher: konservativ bleiben" verstärkt diese Disziplin — bei nicht-existentem Bug ist Nichtstun die richtige Aktion

Diese Disziplin gilt für ALLE Worker-Bienen (1-5), nicht nur den Merger.

### ⚠️ Stufe-0-Pass hat systematische Lücken — 2-Phasen-Polishing Pflicht!

**Erkenntnis aus Session 2026-07-09 (Julian Remote-Control-Video, pvhphecd70Y, 22:57):** Der deterministische Pre-Pass (Stufe 0, Schritt 5a) hat mehrere Hörfehler NICHT gefangen:
- `Tmax`/`TMAX` → `tmux` (9 Vorkommen) — kein Pattern im Polishing-Skript
- `SLGal` → `/goal`, `SlashLOP`/`Slashloop` → `/loop`, `Slash Goal`/`Slash Loop` → `/goal`/`/loop`
- `SLclear` → `/clear`

Erst die Post-Polish-Restfehler-Verifikation (Regex-Check gegen `known-hearing-errors.md`) hat die Lücken aufgedeckt. Danach mussten die Fixes als separate Patches auf den bereits gespeicherten File angewendet werden.

**Pflicht-Workflow für Stufe 0 (deterministisch):**

1. **Phase 1**: Pre-Pass mit `polish_caption()` — Whitespace, Soft-Hyphen, Satzzeichen
2. **Phase 2 (Z W I N G E N D)**: Restfehler-Verifikation mit `post_merge_verification()` aus `references/known-hearing-errors.md` auf den fertigen File-Block
3. **Phase 3**: Treffer als `re.subn` direkt auf den fertigen File anwenden (nicht nur stdout — der File muss aktualisiert werden)
4. **Phase 4**: Erneute Verifikation — `clean == True` muss erreicht sein, sonst sind weitere Patterns in `known-hearing-errors.md` zu ergänzen

Diese 2-Phasen-Struktur war bisher nur für Stufe 3 (Multi-Agent-Merger) explizit dokumentiert — sie gilt aber genauso für Stufe 0. **Lesson**: Auch ohne LLM-Pass MUSS die Heuristik-Liste systematisch gegen den polierten Output gecheckt werden.

**⚠️ KRITISCH: Verifikation muss gegen den TRANSKRIPT-BLOCK laufen, nicht gegen den ganzen File**

**Erkenntnis aus Session 2026-07-09 (pvhphecd70Y Stufe-0-Post-Polish):**

Wenn die Verifikation `re.findall(pattern, whole_file_content)` läuft, schlägt sie fehl weil der **Header-Block selbst Heuristik-Beispiele auflistet** ("`Hermis` → `Hermes`", "`Gitub` → `GitHub`", "`Cloud` → `Claude`" etc. als Doku-Beispiele). Das sind KEINE echten Restfehler, aber das Regex findet sie.

**Konkrete Falle aus Session 2026-07-09:**
- Verifikation auf Transkript-Block (`## [00:00]` bis `<!-- RAW_CAPTION_BLOB`): 0 Treffer — clean!
- Verifikation auf ganzem File-Content: 1× "Hermis" + 1× "Gitub" + 1× "Cloud" Treffer — alle FALSE POSITIVES aus dem Header-Doku-Block
- Falsche Schlussfolgerung möglich: "Restfehler gefunden, Header falsch geschrieben" — dabei IST der Header korrekt, er LISTET ja die Fixes auf

**Lösung — IMMER Block-scoped arbeiten:**

```python
# RICHTIG (Block-scoped):
content = filepath.read_text()
start_idx = content.find("## [00:00]")
end_idx = content.find("<!-- RAW_CAPTION_BLOB")
transcript_block = content[start_idx:end_idx]
# Restfehler-Check NUR auf transcript_block

# FALSCH (führt zu false-positives wenn Header Heuristik-Beispiele listet):
content = filepath.read_text()
# Check auf ganz content → findet die Doku-Beispiele im Header-Block
```

**Faustregel für die Königin:** Trenne den Transkript-Block sauber ab, checke NUR diesen. Header und RAW-Blob sind explizit OUT-OF-SCOPE für Restfehler-Checks. Wer seinen Header mit "Was wurde gemacht: Hermis → Hermes" beschreibt, darf nicht durch seine eigene Doku getäuscht werden.

**Wenn der Header Doku-Beispiele enthält** (was bei Stufe-3-Files normal ist), MUSS der Block-scope explizit gesetzt werden, sonst sieht jedes Mal so aus als hätte der Merger versagt.

### ⚠️ Slash-Regex mit \b-Word-Boundary funktioniert NICHT für `/loop`, `/goal`, etc.

**Symptom:** `re.findall(r"\b/loop\b", text)` gibt `0` zurück, obwohl `/loop` definitiv im Text steht.

**Ursache:** Python's `\b` matcht Word-Boundaries nur zwischen `\w` (= `[a-zA-Z0-9_]`) und Non-Word-Characters. Der Slash `/` ist ein Non-Word-Char, also ist `/loop` von Non-Word-Boundaries umgeben — `\b` matched davor und danach nicht.

**Falsch (gibt 0 zurück):**
```python
len(re.findall(r"\b/loop\b", text))  # → 0
len(re.findall(r"\b/goal\b", text))  # → 0
```

**Richtig (Slash escapen statt \b nutzen):**
```python
len(re.findall(r"/loop", text))    # → 2
len(re.findall(r"/goal", text))    # → 2
len(re.findall(re.escape("/loop"), text))  # → 2 (noch sauberer)
```

**Gilt für alle Slash-Commands:** `/loop`, `/goal`, `/compact`, `/clear`, `/resume`, `/AGs`, `/help`, etc.

Lesson: Beim Verifizieren von Slash-Commands immer `re.escape(name)` oder nackten Slash ohne `\b` nutzen. Die `POST_MERGE_PATTERNS` in `references/known-hearing-errors.md` haben diesen Fehler NICHT (sie nutzen die Slash-Commands direkt ohne `\b`), aber ad-hoc Verification-Snippets brauchen den Fix.

## Verification

Nach jedem Run prüfen:
- [ ] Datei existiert in `~/docs/youtube/`
- [ ] YAML-Frontmatter ist valide
- [ ] Wortzahl plausibel (Duration × ~220 Wörter/Min für Sprache, ~150 für Auto-Caption)
- [ ] Erste `## [00:00]` Section ist da
- [ ] Auto-Caption-Warnung im Header (falls zutreffend)
- [ ] **Polishing-Status im Header sichtbar** (Stufe 0/1/2/3 + was wurde gemacht)
- [ ] **Wortzahl-Drift < 5%** wenn Stufe 1-3 poliert wurde (sonst Halluzinations-Warnung)
- [ ] **Raw-Blob vorhanden** (Schritt 5e) — Hidden HTML-Comment am Dateiende
- [ ] **Bei Stufe 3: Post-Merger-Restfehler-Check** — `post_merge_verification()` aus `references/known-hearing-errors.md` gegen den polierten Text laufen lassen. Compound-Word-Varianten (MCPS, Cloud MDatei, Superagent) separat checken.
- [ ] **Bei Stufe 0 (deterministisch): Trotzdem Post-Polish-Verifikation!** Der deterministische Pre-Pass hat Lücken bei CLI-Tools (tmux→Tmax) und Slash-Commands (`/loop`→`SlashLOP`/`Slashgal`/`Slash Loop`). Immer `post_merge_verification()` als Phase-2-Check laufen lassen und Treffer direkt in den File patchen.
- [ ] **After-Delivery-Zweitpass** (nur Stufe 3): Nach 5+ Min warten (Worker-Outputs können nachträglich eintrudeln) erneuten Restfehler-Check laufen lassen. Nachlieferungen als `patch` auf den Final-File anwenden.
- [ ] **Bei Stufe 4 (LLM-Glättung):** Pre-Phase 4.1 Ambiguitäts-Fixes vor LLM-Dispatch anwenden. Post-Phase Wort-Drift ±2%, Eigennamen-Counts unverändert, 0 Füllwort-Reduktionen.

## Beispiel-Tools

```bash
# Quick & dirty: Transcript + Save
python3.12 -c "
from youtube_transcript_api import YouTubeTranscriptApi
from pathlib import Path
import sys, datetime

video_id = sys.argv[1]
api = YouTubeTranscriptApi()

# Caption-Track finden
tracks = list(api.list(video_id))
lang = next((t.language_code for t in tracks if not t.is_generated), tracks[0].language_code)
print(f'Using: {lang}')

# Fetch
transcript = list(api.fetch(video_id, languages=[lang]))

# Save
out = Path(f'/tmp/transcript_{video_id}.md')
current_min = -1
lines = []
for entry in transcript:
    m, s = int(entry.start // 60), int(entry.start % 60)
    if m != current_min:
        lines.append(f'\n## [{m:02d}:{s:02d}]\n')
        current_min = m
    lines.append(entry.text.replace(chr(10), ' ').strip())
out.write_text('\n'.join(lines))
print(f'Saved: {out} ({out.stat().st_size} bytes)')
"
```

## Siehe auch

- `media-tools` — übergeordnetes Media-Skill-Set (GIF, Audio, Music)
- `youtube-content` — wenn nur Zusammenfassung/Blog-Post aus Transkript gewünscht
- `system-documentation` — Skill zum Dokumentieren in `~/docs/`
- `references/worker1-inhalt-methodology.md` — Vollständige Worker-1-Methodik (Inhalt + Satzzeichen + Minuten-Marker)
- `references/worker2-stil-methodology.md` — Vollständige Worker-2-Methodik (Eigenname-Korrektur)
- `references/faktencheck-methodology.md` — Vollständige Worker-3-Methodik (Faktencheck)
- `references/merger-methodology.md` — Vollständige Worker-4-Methodik (Finale Zusammenführung mit Post-Merge-Verifikation, Compound-Word-Varianten-Disambiguierung, WT/VT/Vault-Auflösung, Restfehler-Check)
- `references/known-hearing-errors.md` — Such-Matrix mit Regex-Patterns für Post-Merger-Verifikation
- `scripts/stufe0_polish_workflow.py` — Vollständiges, lauffähiges 2-Phasen-Stufe-0-Workflow-Skript (Metadaten via oEmbed+curl + deterministisches Polishing + Post-Polish-Patch-Phase gegen Lücken-Patterns)
- `templates/stufe4_schwarm_delegation_prompts.md` — Stufe-4 (LLM-Glättung) Workflow-Plan mit 5 Sub-Phasen, gemessene Performance, Lessons Learned
- `templates/stufe4_worker5_prompt.md` — Vollständiger Worker-5-Briefing-Text für Stufe-4 LLM-Glättung mit strikten Constraints
# Worker-4-Methodik: Finale Zusammenführung (Merger)

## Wann einsetzen

Worker 4 (Merger) ist der letzte Schritt in **Stufe 3** der Caption-Polishing-Pipeline.
Er startet NACH Fertigstellung aller drei parallelen Worker (Inhalt, Stil, Faktencheck) und führt deren Outputs zu einem finalen, korrigierten Transkript zusammen.

## Inputs (3+1 Dateien, kann variieren)

Der Merger bekommt **bis zu vier** Eingaben:

| # | Datei | Inhalt | Format | Hinweis |
|---|-------|--------|--------|---------|
| 1 | `/tmp/yt_polish_output_inhalt.md` | Satzzeichen + Absätze + Minuten-Marker | `===START_INHALT===` / `===END_INHALT===` | MUSS existieren (Basis) |
| 2 | `/tmp/yt_polish_output_stil.md` | Eigennamen-korrigierter Text | `===START_STIL===` / `===END_STIL===` | MUSS existieren |
| 3 | `/tmp/yt_polish_output_faktencheck.md` | Validierungs-Report + Hörfehler-Liste | Freies Markdown mit `===FAKTENCHECK_REPORT===` | KANN fehlen (Worker-Timeout) |
| 4 | (optional) `/tmp/yt_polish_description.txt` | YouTube-Description | Freier Text | Fehlt → kein Description-Kontext |

**3 (Faktencheck) kann fehlen.** Der Worker kann timeouts haben. Der Merger muss ohne ihn weiterarbeiten — siehe „Worker kann nicht liefern" unten.

## Worker-Output-Convention: Status-Block MUSS in der Datei stehen

> **KRITISCH:** Worker schreiben ihren `===FIXES===`-Status-Block NUR dann korrekt, wenn er **IN der Datei** steht, nicht nur auf stdout. Der Merger liest die Dateien, nicht stdout. Ein Worker, der Fixes nur auf stdout meldet, zwingt den Merger, die Fixes aus dem Gedächtnis zu raten.

Erwartetes Format IN der Datei (hinter `===END_<WORKER>===`):

```text
===STATUS_STIL===
Gefixt: OpenCla→OpenClaw (20x), Cloud Code→Claude Code (7x)
Wörter: 7374
Minuten-Marker: 37
Wort-Drift: -0.1%
===END_STATUS_STIL===
```

Wenn ein Worker keinen Status-Block in der Datei hinterlässt, muss der Merger die Fix-Liste aus dem Text-Diff ableiten — aufwändiger, aber machbar.

## Workflow

### Schritt 1: Priorität festlegen

Die **Basis** ist immer der **INHALT-Worker** (Worker 1), weil er:
- Die Minuten-Marker korrekt gesetzt hat
- Satzzeichen und Absätze strukturiert hat
- Die Sprech-Charakteristik erhalten hat

Der **STIL-Worker** (Worker 2) hat Eigennamen korrigiert, OHNE Satzzeichen/Marker zu setzen.
Der **FAKTENCHECK** (Worker 3) hat nur einen Report, keinen Text — liefert zusätzliche Korrektur-Hinweise.

**Faustregel:** INHALT als Struktur-Base, STIL als Korrektur-Layer, FAKTENCHECK als Quality-Gate.

### Schritt 2: STIL-Korrekturen auf INHALT anwenden

Der Merger hat zwei Möglichkeiten:

**Option A — Parst die Fix-Liste aus Worker 2 und wendet sie auf das INHALT-Segment an:**
- Extrahiere die `===FIXES===`-Sektion aus `yt_polish_output_stil.md`
- Wende fixierte Begriffe als `replace()` auf das INHALT-Segment an
- Vorteil: Deterministisch, nachvollziehbar
- Nachteil: Erwischt nicht alle Fälle, wenn Worker 2 Regex-Patterns verwendet hat

**Option B — Nimmt den STIL-Text als Ganzes und übernimmt nur Korrekturen (empfohlen):**
- Behalte die INHALT-Struktur (Marker + Absätze + Satzzeichen)
- Für jeden von Worker 2 gefixten Begriff: `suchen + ersetzen` im INHALT-Segment
- Nutze die Patterns aus der Fix-Liste + ggf. die `known-hearing-errors.md`-Patterns

**Empfohlenes Pattern (kopierfertig):**

```python
import re

def apply_fixes(base_text: str, fix_patterns: list[tuple]) -> tuple[str, int]:
    """Wendet (pattern, replacement)-Paare auf base_text an.
    Liefert (korrigierter_text, anzahl_fixes)."""
    text = base_text
    total = 0
    for pattern, replacement in fix_patterns:
        text, n = re.subn(pattern, replacement, text)
        total += n
    return text, total
```

### Schritt 3: FAKTENCHECK-Findings integrieren

Der FAKTENCHECK kann enthalten:
- **Hörfehler, die Worker 2 übersehen hat** => Muss Worker-2-Fix-Liste erweitern
- **Description-Tag-Diskrepanzen** (Tags die im Transkript fehlen) => Im Header/Footer notieren
- **Zeitstempel-Warnungen** => Marker-Positionen prüfen
- **Attribution-Fehlt-in-Transkript** => Nicht korrigieren (Creator hat Wort nicht ausgesprochen), aber in Metadaten vermerken

**Priority-Stufen für Faktencheck-Findings:**

| Finding | Aktion |
|---------|--------|
| Hörfehler (Name verhunzt) | Korrigieren (in voller Pipeline sofort) |
| Compound-Word-Variante | Gegen `known-hearing-errors.md`-Matrix prüfen |
| Tag-Diskrepanz | Im Header vermerken (nicht im Text ändern) |
| Attribution fehlt | Keine Änderung — ist OE-Entscheidung des Creators |
| Zeitstempel-Drift < 5% | Akzeptieren, kein Handlungsbedarf |
| Zeitstempel-Drift > 10% | Marker-Position neu einmessen |

### Schritt 3b: Worker kann nicht liefern (Fallback-Strategie)

Wenn einer oder mehrere Worker nicht geliefert haben (Timeout, Hänger, leerer Output):

**Fallback-Regeln (priorisiert):**

| Situation | Aktion | Beispiel aus dieser Session |
|-----------|--------|----------------------------|
| Nur Faktencheck fehlt | Inhalt+Stil mergen, Faktencheck-Notiz im Header | V4 (10 Skills, 42:48, 8.758 Wörter) — 0 Restfehler trotz fehlendem Faktencheck |
| Nur Inhalt fehlt | Stil als Struktur-Base nehmen, Marker per Word-Index-Methode setzen | Selten — Inhalt ist einfachster Worker |
| Stil fehlt | Inhalt + Fixes aus `known-hearing-errors.md` manuell anwenden | Aufwändig, aber machbar |
| Alle drei da | Normaler Merge — kein Fallback | Standardfall |
| Nur 1 Worker geliefert | Als Stufe-2-Output behandeln, Header: „Pipeline unvollständig (N/N geliefert)" | Letzter Ausweg, bisher nie nötig |

**Faktencheck-Timeout ist der häufigste Fallback.** Der Faktencheck-Worker hat den komplexesten Report und braucht am meisten Kontext. In der Session 2026-07-04: 1 von 4 Runs hatte Faktencheck-Timeout beim 42:48/8.758-Wörter-Video.

**Output ohne Faktencheck ist trotzdem gut.** V4-Output hatte 0 Restfehler im polierten Bereich, obwohl Faktencheck fehlte. Der Stil-Worker allein reicht für >95% Korrektur-Abdeckung. Die Description-Cross-Reference kann bei Bedarf manuell nachgeholt werden.

**Header-Flag bei Fallback:**
```yaml
polishing: Stufe 3 (reduziert — Faktencheck-Worker nicht geliefert, Merger aus Inhalt+Stil)
```

### Schritt 3c: Multiple START/END-Marker-Stacks handhaben

Wenn ein Worker mehrmals läuft (z. B. wegen Retry durch Delegation-Framework), kann die Datei **mehrere** `===START_<WORKER>===`...`===END_<WORKER>===`-Blöcke enthalten. Der Merger muss den **letzten gültigen Block** nehmen:

```python
import re

def extract_last_block(text: str, tag: str) -> str:
    """Extrahiert den letzten Block zwischen ===START_<TAG>=== und ===END_<TAG>===."""
    pattern = rf"===START_{tag}===\n(.*?)\n===END_{tag}==="
    matches = re.findall(pattern, text, re.DOTALL)
    if not matches:
        return ""
    return matches[-1].strip()  # Letzten Block = vollständigster Output
```

**Warum den letzten Block?** Bei Retry überschreibt der Worker die Datei nicht — er hängt an. Der letzte Block hat alle vorherigen Iterationen verarbeitet und ist der vollständigste.

### Schritt 4: Post-Merge-Verifikation (zwingend)

Nach dem Merge muss der gesamte Text systematisch geprüft werden:

**4a. Minuten-Marker-Count:**
```bash
grep -c '^## \[' /tmp/yt_v5_output_final.md
# Muss EXAKT video_dauer_in_minuten + 1 sein (z.B. 37 bei 36:24)
```

Achtung (bekannte Falle): `grep -c "^## [0"` zählt NUR Marker von 00:00 bis 09:xx!
Richtig: `grep -c '^## \['`

**4b. Letzten Marker prüfen:**
```bash
grep -E '^## \[' /tmp/yt_v5_output_final.md | tail -1
# Muss ## [MM:00] sein, wobei MM = video_dauer_in_minuten
```

**4c. Word-Count prüfen:**
```bash
wc -w /tmp/yt_v5_output_final.md
# Erwartung: Input-Wortzahl +/- 2% (Drift durch Korrekturen)
```

**Wichtig: Drift kann positiv ODER negativ sein.** Compound-Expansion (Korrekturen wie "Cloud Code" → "Claude Code" fügen 0 Zeichen hinzu, aber "Cloud" → "Claude" fügt 1 Zeichen pro Korrektur zu) kann die Wortzahl leicht erhöhen. Compound-Merges ("den jeder" → "jeden einzelnen Schritt") können sie senken.

| Richtung | Typische Ursache | Beispiel |
|----------|-----------------|----------|
| Negativ (-) | Compound-Merges fassen Wörter zusammen; Subagent-Vokabelabgleiche mit Grenzfällen | -1,6% (5 OpenClaw Usecases) |
| Positiv (+) | Ausgeschriebene/erweiterte Komposita (Cloud-Code → Claude Code expandiert minimal) | +0,6% (Claude Code Skills, 8.758→8.809 Wörter) |
| Kein Drift | Deterministischer Regex-Pass ändert nur Whitespace | 0% (Stufe 0) |

**Absolut-Drift < 5% ist immer OK.** Die Richtung allein ist kein Qualitätsindikator — eine wortzahl-stabile Pipeline kann trotzdem fehlerhaft oder korrekt sein. Nur der Post-Merge-Restfehler-Check ist der echte Qualitätsnachweis.

**4d. Post-Merge-Restfehler-Check mit der Such-Matrix:**

Alle Patterns aus `known-hearing-errors.md` (POST_MERGE_PATTERNS) gegen den finalen Text laufen lassen.

```bash
# Quick-Checks fuer die haeufigsten verbleibenden Fehler:
for pat in 'Cloud' 'Claud' 'Clod' 'Cludt' 'Clot' 'Cloudian' \
           'Volt' 'Wolt' 'VT-Struktur' 'WT-Struktur' 'Wollstruktur' \
           'Excaly Drawrop' 'Excalid Drawrop' 'Brad Plugin' 'Anup Puuccin' 'JGPT' \
           'OpenClock' 'Open Cla' 'Obsidien' \
           'Mark Dateien' 'Markon Datei' 'Markn Dateien' \
           'Kontextordr' 'Brain Dump'; do
  c=$(grep -c -E "$pat" /tmp/yt_v5_output_final.md)
  if [ "$c" -gt 0 ]; then
    printf "%-25s : %d (PROBLEM)\n" "$pat" "$c"
  fi
done
echo "(zero entries = all clean)"
```

**4e. Expected-correct verifizieren:**
```bash
for term in 'Claude Code' 'Claude Cowork' 'Vault' 'CLAUDE.md' \
            'Markdown-Datei' 'Excalidraw' 'BRAT' 'AnuPuccin' \
            'OpenClaw' 'Kontextordner' 'Claudian'; do
  echo "$term: $(grep -c -wE "$term" /tmp/yt_v5_output_final.md)"
done
```

## Merger-Pitfalls (aus der Praxis)

### Compound-Word-Varianten — der haeufigste Restfehler

Ein Fix fuer "Cloud Code zu Claude Code" erwischt automatisch:
- `Cloud Code` (ja)
- `Claud Code` (ja, separates Pattern)

Aber NICHT:
- `Cloud-Code-Skill` (Compound-Adjektiv mit Bindestrich)
- `Clouds Code` (falscher Plural)
- `Claud` am Satzanfang `Claud.` => `Claude.` (Boundary-Pruefung)

**Loesung:** Die erweiterte Heuristik-Liste in `known-hearing-errors.md` deckt alle Varianten ab. Nach dem Merge IMMER `post_merge_verification()` laufen lassen.

### Cloud-Code vs. Claude Code Disambiguierung

Nicht jedes "Cloud Code" meint "Claude Code". Compound-Adjektive wie `Cloud-Code-Skill` (ein von Claude Code erstellter Skill) bleiben als `Cloud-Code-Skill` erhalten.

**Faustregel:**
- Standalone `Cloud Code` => `Claude Code` (Korrektur)
- `Cloud-Code` als Compound-Adjektiv mit Bindestrich => belassen
- `Cloud Code [Substantiv]` => prüfen ob `[Substantiv]` ein Tool-Name ist

### WT/VT/Volt/Woll in Obsidian-Kontext

Bei Obsidian-bezogenen Transkripten wird `Vault` haeufig als `WT`, `VT`, `Volt` oder `V` verhunzt.

**Aufloesungsstrategie:**
1. Stark amputierte Formen (`V`, `WT`, `VT`) => im Kontext checken
2. Wenn Obsidian-Kontext => `Vault`
3. `Volt` => fast immer Obsidian-Vault (phonetisch nah)

**Daten aus der Praxis:** In einem 36-Minuten-Run (NVUCQ-pzBn4) wurden 13 WT/VT/Volt-Stellen zu `Vault` aufgeloest — alle korrekt.

### Minuten-Marker nicht als Korrektur-Ziel setzen

Die Marker (`## [MM:SS]`) duerfen NICHT durch den Merger veraendert werden. Sie sind die Struktur-Base aus Worker 1.
Der gesamte Arbeitsbereich des Mergers ist der TEXT ZWISCHEN den Markern.

### Grep-False-Positive in der Post-Merge-Verifikation

Die Quick-Check-Suchmuster in Schritt 4d/4e erzeugen oft False-Positives, die den Anschein erwecken, es gäbe noch Hörfehler, obwohl alles sauber ist.

**Häufigste False-Positive-Quellen:**

| Suchmuster | Findet auch | Erklärung |
|-----------|-------------|-----------|
| `Vault` | korrekte Vorkommen + `Vault-Struktur` (legitimes deutsches Kompositum) | "Vault-Struktur" ist KEIN Hörfehler — der Sprecher verwendet es als zusammengesetztes Nomen |
| `OpenCla` | `OpenClaw` (korrekt) | grep matched "OpenClaw" weil es "OpenCla" als Substring enthält |
| `Cloud` | `Cloud-Code`, `Cloud-Speicher`, `Cloud-Instanz` (alle teils korrekte Komposita) | Compound-Adjektive mit Bindestrich sind keine Hörfehler |
| `Claud` | `Claudian` (Obsidian-Plugin, korrekt) | "Claud" in "Claudian" ist legitimer Plugin-Name |

**Verifikations-Regel:** Ein grep-Treffer ist nur dann ein echter Hörfehler, wenn der **Kontext** das Wort als verhunzt ausweist. Bei Unsicherheit: `grep -oP '.{50}Suchmuster.{50}'` für Kontext-Ansicht. Ein Treffer in einem Compound-Kompositum mit Bindestrich oder als Teil eines längeren korrekten Worts ist meist kein Hörfehler.

**Speziell: "Vault-Struktur"** ist KEIN Hörfehler. Es ist ein legitimes deutsches zusammengesetztes Nomen, das der Sprecher selbst verwendet ("dann ein Bereich über die Vault-Struktur", "hier die Vault-Struktur in der CLAUDE.md"). Nicht patchen, nicht im Post-Merge-Check flaggen.

### Worker-Status-Block muss in der Datei stehen (nicht nur auf stdout)

Siehe Worker-Output-Convention oben. Dieser Pitfall wiederholt es hier als Merger-Perspektive:

Der Merger hat ZUGRIFF AUF DATEIEN, nicht auf stdout. Wenn ein Worker seinen `===FIXES===`-Block nur auf stdout schreibt (z. B. nach dem Schreiben der Datei noch mal `print("Fixes: …")`), kann der Merger ihn nicht lesen. **Lösung:** Der Worker schreibt den Status-Block IN die Datei, nach `===END_<WORKER>===`. Der Merger parst ihn mit:

```python
import re
def parse_status(text: str, tag: str) -> dict:
    """Parst ===STATUS_<TAG>=== ... ===END_STATUS_<TAG>=== aus Datei-Text."""
    m = re.search(rf"===STATUS_{tag}===\n(.*?)\n===END_STATUS_{tag}===", text, re.DOTALL)
    if not m:
        return {}
    return {"raw": m.group(1).strip()}
```

### Aufräumen von /tmp/ nach Pipeline-Durchlauf

Nach Fertigstellung der Pipeline liegen in /tmp/ mehrere Dateien:

| Datei | Größe | Aufbewahren? |
|-------|-------|-------------|
| `yt_polish_input.txt` | ~30-55 KB | bis Merge abgeschlossen |
| `yt_polish_description.txt` | ~2-5 KB | bis Merge abgeschlossen |
| `yt_polish_output_inhalt.md` | ~30-55 KB | bis Merge abgeschlossen |
| `yt_polish_output_stil.md` | ~30-55 KB | bis Merge abgeschlossen |
| `yt_polish_output_faktencheck.md` | ~5-10 KB | bis Merge abgeschlossen |
| `yt_v5_output_final.md` | ~50-100 KB | Finales Artefakt — in ~/docs/youtube/ verschieben |
| `yt_v5_new_header.md`/`yt_v5_header_*.md` | ~3-5 KB | Nach Header-Bau löschen |
| Alle Python-Skripte (`yt_v*_dump.py`, `yt_v*_polish.py`) | ~1-3 KB | Sofort nach Nutzung löschen |

**Cleanup-Befehl nach finalem Save:**
```bash
rm -f /tmp/yt_v*_*.md /tmp/yt_v*_*.txt /tmp/yt_v*_*.json /tmp/yt_v*_new_header.md /tmp/yt_polish_*.md /tmp/yt_polish_*.txt
```

Hinterlasse KEINE Dateien in /tmp/ von der Pipeline — sie werden sonst beim nächsten Run mit der alten Stufe-0-Version verwechselt.

### ⚠️ /tmp/ TTL mid-pipeline — Worker-Outputs können verschwinden

**Symptom:** `/tmp/yt_v*_*.md`-Dateien sind plötzlich leer oder verschwunden, obwohl Worker sie vor <15 Minuten geschrieben hatten. Betroffen sind insbesondere Systeme mit `systemd-tmpfiles` oder `tmpreaper`.

**Erfahrungsbericht (Session 2026-07-04, k2p6WprtzFI):** Der Merger las insgesamt 3× erfolgreich die Worker-Outputs, dann zwischen einem tool-call-Aufruf und dem nächsten waren ALLE `/tmp/yt_v6_*`-Dateien gelöscht (sichtbar als `ls: cannot access … No such file`). Wiederholte Leseversuche scheiterten. Kein Benutzer-TTY war beteiligt — die Pipeline lief als async delegator-gestarteter Subagent.

**Ursache:** `/tmp/` wird auf manchen Hosts per `systemd-tmpfiles --clean` automatisch geleert. Faktoren:
- Linux-Standard-TTL für `/tmp`-Dateien: 10 Tage (Age), aber durch `tmpfiles.d`-Konfiguration auf 1h-24h gesenkt
- Session-spezifisch: Hermes-Infrastruktur kann `/tmp/` nach Session-Ende oder bei Umgebungs-Wechseln leeren
- Beim Delegation über `delegate_task` ist unklar, ob der Host des Merger-Workers der gleiche ist wie der der Produzenten — unterschiedliche `/tmp/`-Namespaces möglich

**Recovery-Strategie (Priorität):**

| # | Strategie | Aufwand | Erfolgswahrscheinlichkeit | 
|---|-----------|---------|--------------------------|
| 1 | **Existierende Doc-Datei nutzen** (empfohlen) | Gering — nur read_file | Hoch — falls Pipeline bereits in vorheriger Session gelaufen |
| 2 | Worker-Output aus Conversation-Memory rekonstruieren | Mittel — grep durch Session-Log | Mittel — nur falls vollständige Worker-Outputs Inline dokumentiert |
| 3 | Worker neu starten | Hoch — volle Pipeline-Zeit | Sehr hoch — garantiert korrekt |

**Strategie 1 im Detail:**

Wenn `/tmp/`-Dateien fehlen, aber eine Datei in `~/docs/youtube/` existiert:
```bash
# Prüfen ob Doc bereits existiert:
ls -la ~/docs/youtube/YYYY-MM-DD_*_k2p6WprtzFI.md
# Falls ja: transkribierte Sektion extrahieren
grep -n '^## \[' ~/docs/youtube/YYYY-MM-DD_*_k2p6WprtzFI.md | head -1
# → extrahiere ab erstem Minuten-Marker bis zum RAW_CAPTION_BLOB-Kommentar
```

Dann:
1. Qualitätsaudit laufen lassen (Schritt 4d/4e)
2. Verbleibende Residualfehler patchen
3. Fertig melden mit Hinweis: "Recovery aus ~/docs/youtube/ nach /tmp-Cleanup"

**Besonderheit bei Strategie 1:** Der Output kann bereits poliert sein — das Audit prüft nicht mehr den Merge-Prozess (da bereits abgeschlossen), sondern nur noch, ob das resultierende Artefakt restfehlerfrei ist. Ein einzelner Restfehler (`Clord`→`Claude` im Fall k2p6WprtzFI) ist vertretbar — aber dokumentieren dass er gefunden und gefixt wurde.

**Prävention:** Bei Stufe-3-Pipelines die Worker-Outputs NACH Fertigstellen des Mergers in eine Nicht-/tmp-Datei sichern, z.B. `/home/bratan/.hermes/scratch/<session_id>/`. Oder den Merger als Teil des Delegation-Calls ausführen (Monolith statt async), sodass /tmp/ vom gleichen Host stammt.

## Bewertung der Merge-Qualitaet

| Metrik | Gut | Akzeptabel | Warnung |
|--------|-----|------------|---------|
| Minuten-Marker erhalten | 100% | >95% | <95% |
| Wortzahl-Drift | <2% | <5% | >5% |
| Restfehler (Post-Merge-Check) | 0 | 1-3 | >3 |
| Faktencheck-Warnungen bearbeitet | alle | die meisten | ignoriert |

## Output-Format

Die finale Datei wird nach `/tmp/yt_v5_output_final.md` geschrieben:

```markdown
## [00:00]

<geglaetteter und korrigierter Text>

## [01:00]

...
```

Keine `===START/END===-Wrapper` am Ende — der Output ist direkt verwendbar.
Auf stdout nach Fertigstellung:

```text
- ANZAHL_WOERTER: <Zahl>
- MINUTEN_MARKER: <Anzahl>
- EIGENNAME_FIXES_TOTAL: ~<Zahl>
```

## Praxis-Daten (gesammelt aus mehreren Runs)

| Video | Dauer | Wörter | Marker | Fixes | Restfehler | Worker-Zeit | Merger-Zeit | Total |
|-------|-------|--------|--------|-------|------------|-------------|-------------|-------|
| Claude Code 8 Best Practices (9PFTLjuELs8) | 26:34 | 5.520 | 27/27 | ~169 | 2 (MCPS→MCP-Server) | ~180s | ~80s | ~260s |
| 5 OpenClaw Usecases (a_SkNoVXBCo) | 22:14 | 4.862 | 23/23 | ~50+ | 0 | ~160s | ~70s | ~230s |
| Top 10 Claude Code Skills (Vx6QlEhyybQ) | 42:48 | 8.809 | 43/43 | ~120 | 0 (Faktencheck fehlte) | ~200s | aufwändiger (Fallback) | ~5 Min |
| Obsidian+Claude Code: Zweites Gehirn (NVUCQ-pzBn4) | 36:24 | 7.426 | 37/37 | ~105 | 0 | ~210s | ~240s | ~7,5 Min |
| KI-Betriebssystem mit Claude Code (k2p6WprtzFI) | 42:30 | 9.180 | 43/43 | ~190 | 0 (nach Clord→Claude) | — | Recovery aus ~/docs/youtube/ | — |
| Remote Control (pvhphecd70Y) — Stufe 0→3 nachpoliert | 22:57 | 4.903 | 23/23 | ~140+ | 0 | ~620s (3 parallel) | ~243s | ~7 Min |

**Muster:** Pro ~200 Wörter ≈ 1 Sekunde Worker-Zeit. Der Merger skaliert sublinear — je mehr Worker-Output, desto mehr muss er lesen/vergleichen. Faktencheck-Timeout tritt bei sehr langen (>8.000 Wörter) Transkripten auf.

## Briefing-Disziplin: Merger MUSS Annahmen der Königin verifizieren

**Erkenntnis Session 2026-07-09 (pvhphecd70Y Stufe-3):**

Die Bienenkönigin hat in einem Briefing an die Merger-Biene geschrieben "Worker 2 hat 'Claudee' als BUG eingeführt (zu aggressive Ersetzung), das muss zurück zu 'Claude'." Diese Annahme basierte auf einem **Sample-Read** der ersten 50 Zeilen von Worker 2's Output-File (was wie "Claudee Code" aussah).

Tatsächliche Verifikation:
- Worker 2's **Final-File** hatte 0× `Claudee` im Transkript-Block (Worker 2 hat den selbst-erzeugten Bug in seiner eigenen zweiten Iteration eliminiert)
- Die Merger-Biene hat das Briefing **richtig hinterfragt** statt blind auszuführen

**Lehren:**

| # | Wer | Lektion |
|---|-----|---------|
| 1 | Königin | Files GLEICH nach Worker-Lieferung **vollständig** checken, nicht nur Sample-Reads. Sample-Reads können zu falschen Annahmen führen. |
| 2 | Königin | Wenn ein Briefing einen Bug beschreibt, vorher durch `grep -c` / Count verifizieren — nicht visuell aus Sample-Zeilen extrapolieren. |
| 3 | Merger | Bei Briefing-Annahmen die ungeprüft sind: selbst verifizieren (z.B. `grep -c "Claudee" Worker-File`). Wenn der angebliche Bug nicht existiert, das transparent kommunizieren statt ihn zu "fixen". |
| 4 | Beide | Die Anweisung "Wenn unsicher: konservativ bleiben" verstärkt die Disziplin — bei nicht-existentem Bug ist Nichtstun die richtige Aktion. |

**Konkret für künftige Königinnen-Briefings an Merger:**

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

## Siehe auch

- `known-hearing-errors.md` — Vollstaendige Regex-Such-Matrix fuer Post-Merge-Verifikation
- `youtube-transcript-saver/SKILL.md` — Stufe-3-Pipeline-Uebersicht
- `worker1-inhalt-methodology.md` — Worker-1-Methodik (Marker + Satzzeichen)
- `worker2-stil-methodology.md` — Worker-2-Methodik (Eigennamen-Korrektur)
- `faktencheck-methodology.md` — Worker-3-Methodik (Validierung)

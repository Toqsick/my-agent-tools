# Pattern 10: MERGER Worker — Deep Dive

**Source:** Transkript-Polishing-Schwarm Session, 2026-07-09
**Proven:** 4905 Wörter Final-Output, -0.02% Drift, 23/23 Minuten-Marker, 0 Heuristik-Reste

## When This Pattern Applies

Use Pattern 10 (MERGER Worker / Konsolidierungs-Biene) when:

- Königin hat **N≥2 parallele Worker-Bienen dispatched** mit disjunkten Aufgaben (z.B. Inhalt + Stil + Faktencheck)
- Das **gewünschte Endprodukt ist EIN einzelnes poliertes Artefakt** (nicht N separate Artefakte)
- Workers liefern **konkurrierende/komplementäre Fixes** für dasselbe Quell-Material
- Königin **will den Merger-Output nicht selbst konsolidieren** (Zeit/Kontext-Gründe)

**Nicht anwenden wenn:**
- N=1 Worker (kein Merge nötig)
- Worker-Outputs widersprechen sich fundamental
- Merge-Logik erfordert domänenspezifisches Wissen, das der MERGER nicht hat

## The 4-Step Methodik (Verdichtet)

```
1. BASIS-WAHL     → Einen Worker-Output als Basis wählen, WARUM dokumentieren
2. CLAIMS VERIFY  → Briefing-Claims gegen tatsächliche Outputs prüfen (grep -c)
3. PUNKTUELLE     → Fixes aus anderen Workern punktuell übernehmen (keine Concatenation)
   FIXES
4. POST-MERGE     → Word-boundary regex, alle Heuristik-Patterns prüfen, DRIFT messen
   GATE
```

## Briefing-Template für MERGER (Königin-Perspektive)

Wenn die Königin einen MERGER dispatched, MUSS das Briefing folgende Sektionen enthalten:

```markdown
## INPUTS
- /path/to/output_worker1_<topic>.md (N Wörter, <Rolle>)
- /path/to/output_worker2_<topic>.md (N Wörter, <Rolle>)
- /path/to/output_worker3_<topic>.md (N Wörter, <Rolle>)
- /path/to/input_baseline.md (N Wörter, Baseline für Drift-Vergleich)

## DEINE AUFGABE
1. **Basis wählen**: <Worker N> als Basis weil <Begründung>
2. **Worker-X-Fixes übernehmen**: <Liste der spezifischen Fixes>
3. **Worker-Y-Findings umsetzen**: <Liste der kritischen Findings>
4. **Restfehler-Post-Verification**: <Heuristik-Liste>

## MERGER-METHODIK (strict)
- <Strukturelement 1, z.B. "Minuten-Marker bleiben 1:1"> bleiben 1:1
- <Strukturelement 2, z.B. "Reihenfolge der Sätze"> bleibt 1:1
- KEINE inhaltlichen Änderungen, keine Zusammenfassung
- Wort-Drift-Limit: ±X% zur Baseline

## KRITISCH
- **Briefing-Claims IMMER verifizieren** — wenn die Königin sagt "Worker X hat Bug Y", erst `grep -c "<Bug-Pattern>" output_workerX.md`, dann fixen. Wenn 0 Vorkommen → dokumentieren + SKIP.
- **Word-boundary regex für Heuristik-Verifikation** — nicht `grep "Cloud"`, sondern `grep "\bCloud\b"` oder `grep -E "(?<![\w-])Cloud(?![\w-])"`.
- **Konservativ bei unklaren Findings** — wenn Faktencheck "könnte X oder Y sein" sagt, NICHT raten. Im Final-Report mit Begründung dokumentieren.

## OUTPUT-FORMAT
===START_MERGER===
<gemergter polierter Output>
===END_MERGER===

===STATUS_MERGER===
Woerter: NNNN
Gefixt: <Liste>
Konservativ NICHT gefixt: <Liste mit Begründungen>
Minuten-Marker: N/N
Wort-Drift: ±X%
===END_STATUS_MERGER===

## WICHTIG
Du schreibst NUR den <Output-Block> nach <local_file>. Den Einbau in den <Original-Artefakt> übernehme ich (die Königin).
```

## Word-Boundary Regex Patterns (Heuristik-Verifikation)

| Substring-Suche (FALSCH) | Word-Boundary-Suche (RICHTIG) | Was es fängt |
|---|---|---|
| `grep "Cloud"` | `grep "\bCloud\b"` | Standalone "Cloud" (nicht in "Cloud Code", "Claude-Cloud") |
| `grep "Claudee"` | `grep "\bClaudee\b"` | Eigenname-Variante |
| `grep "erknüpfen"` | `grep "\berknüpfen\b"` | Hörfehler — vermeidet "verknüpfen"-Substring-Match |
| `grep "impress"` | `grep "\bImpressum\w*\b"` | Compound-Variante (Impressum, Impressumsmaske, etc.) |

**Generisches Pattern für Eigennamen mit optionalem Suffix:**
```bash
grep -oE "(?<![\w-])Eigenname(?![\w-])" file.md
```
Der Lookbehind `(?<![\w-])` und Lookahead `(?![\w-])` schließen Wort-Boundary UND Bindestrich-Verbindungen aus. Nützlich wenn du "Cloud" matchen willst, aber NICHT "Cloud-Code", "Cloudflare", "Cloudinary".

## Worked Example: Transkript-Polishing (2026-07-09)

**Setup:**
- 3 Worker-Outputs (Inhalt 4964 Wörter, Stil 4902 Wörter, Faktencheck Report 27 Findings/12 kritisch)
- Baseline: input_transcript.md (4906 Wörter)
- Wort-Drift-Limit: ±2% (4808-5004)

**Phase 1 — Basis-Wahl:**
Worker 2 (Stil) gewählt weil:
- 95 korrekte "Claude" Vorkommen (höchste Eigenname-Korrektheit)
- 0 verbleibende "Cloud" Hörfehler
- Alle Heuristik-Patterns bereits gefixt

**Phase 2 — Claims Verification:**

| Briefing-Claim | Verifikation | Ergebnis |
|---|---|---|
| "Worker 2 hat 'Claudee' eingeführt" | `grep -c "Claudee" output_worker2_stil.md` | **0** → SKIP (Briefing-Fehler) |
| "Worker 2 hat 'Clot', 'Clode', 'Cludier'" | nur in Worker-2-STATUS-Footer (Self-Report) | **0 im Transcript** → SKIP |
| "T-Max quasi ein Terminal" | `grep -c "T-Max" output_worker2_stil.md` | 0 → bereits gefixt → SKIP |

**Lesson:** Hätte ich den "Claudee"-Fix angewendet, hätte ich "Claude" → "Claudee" → ... produziert. Briefing-Claims sind IMMER zu verifizieren.

**Phase 3 — Punktuelle Fixes:**

| Befund | Quelle | Übernommen? |
|---|---|---|
| `closed starten` → `claude starten` | Worker 3 | ✅ (1x) |
| `Impressummatte` → `Impressumsmaske` | Worker 3 | ✅ (1x) |
| `DDatei` → `Datei` (Phrase umgebaut) | Worker 1 | ✅ (1x) |
| `Anmoldeformular` → `Anmeldeformular` | Worker 1 | ✅ (1x) |
| `züllen` → `füllen` | Worker 1 | ✅ (1x) |
| `debugen` → `debuggen` | Worker 1+3 | ✅ (1x) |
| `Modis` → `Modi` | Worker 1 | ✅ (1x) |
| `blaulen` → `blauen` | Worker 1 | ✅ (1x) |
| `Das heiß` → `Das heißt` | Worker 1 | ✅ (1x) |
| `ca. Eine` → `ca. eine` | Worker 1 | ✅ (1x) |
| `erknüpfen` → `verknüpfen` | Worker 1 | ❌ (bereits von Worker 2 still korrigiert — keine Aktion) |
| `Textag` (unklar) | Worker 3 | ❌ konservative SKIP |
| `Resent` (unklar) | Worker 3 | ❌ konservative SKIP |
| `KFM2` (unklar) | Worker 3 | ❌ konservative SKIP |
| `[musik]` (UI-Element, kein Caption-Artefakt) | Worker 3 | ❌ konservative SKIP |

**Phase 4 — Post-Merge Gate:**

```bash
# 1. Minuten-Marker
grep -cE '^## \[[0-9][0-9]:[0-9][0-9]\]' _transcript_only.md
# → 23 ✅

# 2. Wort-Drift
wc -w _transcript_only.md
# → 4905 (-0.02% vs. Baseline 4906) ✅

# 3. Eigennamen
grep -E "\bClaudee\b" _transcript_only.md
# → 0 ✅
grep -E "\bCloud\b" _transcript_only.md
# → 0 ✅

# 4. Heuristik-Reste (alle word-boundary)
for pattern in 'Claudee' 'Cloud Code\b' 'Hermis' 'Gitub' 'T-Max' 'slem Control' \
               'Rustinger' 'Hey Claud' 'Clot\b' 'debugen' 'Impressummatte' \
               'Anmoldeformular' 'züllen' 'erknüpfen\b'; do
  grep -cE "$pattern" _transcript_only.md
done
# → alle 0 ✅

# 5. Worker-3-kritische Findings (alle adressiert)
for pattern in 'SLRemote' 'slem Control' 'Slash Clear' 'SlashG' 'T-Max' \
               'Rustinger' 'closed starten' 'Anmoldeformular' 'Cludier' \
               'Impressummatte' 'züllen' 'debugen'; do
  grep -c "$pattern" _transcript_only.md
done
# → alle 0 ✅
```

## Häufige Fehler beim MERGER-Worker

| Fehler | Symptom | Fix |
|---|---|---|
| Briefing-Claim blind angewendet | Output hat Bugs, die im Briefing erwähnt waren, aber Worker N hatte sie nie | Pattern 10 Schritt 2: IMMER `grep -c` vor dem Fix |
| Substring-Match für Heuristik | Verifikation meldet 5 verbleibende Bugs, aber tatsächlich sind es 0 | Pattern 10 Schritt 4: word-boundary regex |
| Workers konkateniert statt punktuell gemergt | Output ist Misch-Masch, doppelte Sätze, inkonsistente Eigennamen | Pattern 10 Schritt 1+3: EIN Worker als Basis, andere punktuell |
| Scope-Creep (MERGER schreibt ins Original-Artefakt) | MERGER überschreibt Dateien, die Königin verwalten sollte | Briefing muss Scope klar abstecken: "Du schreibst NUR nach <local_output>, Original-Artefakt handled Königin" |
| Unklare Findings "gefixt" | Output hat plausible aber falsche Korrekturen | Pattern 10 Schritt 3: konservativ skippen + Final-Report dokumentieren |

## Related Skills

- `multi-agent-cluster-patterns` — Pattern 10 lebt hier (diese Reference ist Deep-Dive)
- `orchestration/multi-agent-pitfalls-cheatsheet` — TRIGGER-WATCHLIST, Pitfalls #5 (Phantom-Fixes) und #29 (Summary ≠ File) sind direkte Geschwister der MERGER-Pitfalls
- `multi-agent-orchestration` — sibling für Research-Cluster
- `subagent-driven-development` — sibling für Code-Cluster
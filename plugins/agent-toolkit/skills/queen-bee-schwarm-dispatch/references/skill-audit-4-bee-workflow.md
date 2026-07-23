# Skill Audit — 4-Bee Orthogonal Workflow (Validated 2026-07-16)

**Kontext:** Vollständiger Skill-Library-Audit der Hermes-Bibliothek
(298 aktive Skills, ~980K Tokens, 85 Scripts).

**Pattern:** Queen dispatches **4 orthogonale Scout-Bienen** (disjunktes Scope),
erhebt parallel **eigene Baseline**, fixt P0/P1 nach Cross-Check,
und dispatches **2 Verify-Bienen** für Post-Fix-Validierung.

---

## Die 4 Bienen-Rollen (disjunkt, überlappungsfrei)

| Biene | Scope | Frage | Metrics |
|-------|-------|-------|---------|
| **A — Frontmatter/Description** | YAML-Parse, Description-Length, Missing Fields | "Welche Skills sind unsichtbar oder broken?" | Parse-Errors, <30 chars, >150 chars, missing author/version |
| **B — Trigger/Obsolescence** | Trigger-Coverage, Stale Skills, Weak Triggers | "Welche Skills werden nie geladen?" | Trigger-Phrase-Exists, Description <60 chars + no trigger |
| **C — Structure/Size** | Monoliths, File-Layout, Scripts-per-Skill | "Welche Skills sind zu gross oder falsch strukturiert?" | >500 Zeilen, files/scripts per skill, file-structure-anomalies |
| **D — Overlap/Duplicates** | Gleiche Descriptions, Gleiche Topic-Namen | "Welche Skills überschneiden sich?" | Levenshtein < 0.3 Description-Similarity, topic-name matches |

### Warum genau diese 4?

1. **Jede Biene braucht eine andere Lesestrategie:**
   - A liest nur YAML-Frontmatter (schnell)
   - B liest Frontmatter + Body-Trigger (synthetisch)
   - C liest Filesystem-Struktur (ls/find)
   - D liest nur Descriptions + Names (String-Matching)

2. **Keine zwei Bienen lesen die gleiche Datei zur gleichen Zeit.**
   - A + B lesen SKILL.md, aber für verschiedene Felder → kein Konflikt
   - C liest Filesystem (stat)
   - D liest Description-Strings (kein File-Write)

3. **Queen-Baseline deckt alle 4 ab** → Cross-Check erkennt Self-Report-Lücken.

---

## Briefing-Architektur

Jede Biene bekommt ein Briefing mit:

### Identity
```
Du bist Biene A (Frontmatter-Auditor) in Yunos Skill-Audit-Schwarm.
```

### Context (kurz, präzise)
```
KONTEXT:
- Yuno auditert ~298 Skills unter ~/.hermes/skills/
- Die Queen erhebt parallel Baseline-Metriken
- Dein Job: ORTHOGONAL zu Queen + anderen Bienen — überschneide dich NICHT
```

### Tasks (nummeriert, mit Pfad + Aktion)

```
DEINE TASKS (ALLE READ-ONLY):
1. Parse ALLE 298 SKILL.md mit python3 yaml.safe_load → zähle Errors
2. Für jedes SKILL.md: description-Länge messen → <30, 30-60, 60-100, 100-150, >150
3. Für jedes SKILL.md: fehlt author/version? Zähle
4. Berichte: Liste der broken Files (Name, Category, Error)
5. Berechne: Wie viele Skills sind "unsichtbar" (desc < 30 chars)?
```

### Output-Constraints (HART)
```
OUTPUT-CONSTRAINTS (PFLICHT — NICHT VERHANDELBAR):
- 0 mid-sentence boldface
- 0 em-dashes (—)
- Output: REIN TEXT in deiner Antwort (kein File-Write)
- Max 800 Wörter
- SELF-REPORT am Ende: "N tool-calls, M findings"
- Sprache: Deutsch
```

### Tool-Limit + Self-Verify
```
MAX <12> terminal-calls. Nach 12 → Synthese mit was du hast.
Self-Verify: Alle Fakten mit Pfadangabe. Nichts erfinden.
Lieber "konnte nicht prüfen" als halluzinieren.
```

---

## Queen Baseline Pre-Execute (parallel zu Bienen)

Während die 4 Bienen dispatched sind, erhebt die Queen ihre eigene Baseline:

```bash
cd ~/.hermes/skills

# Baseline A: Description-Length-Distribution
python3 -c "
import yaml, glob
stats = {}
for f in glob.glob('**/SKILL.md', recursive=True):
    if '.archive/' in f: continue
    with open(f) as fh:
        parts = fh.read().split('---', 2)
        fm = yaml.safe_load(parts[1])
    d = len(str(fm.get('description',''))) if isinstance(fm,dict) else -1
    bucket = '<30' if d<30 else '<60' if d<60 else '60-200' if d<=200 else '200-600' if d<=600 else '>600'
    stats[bucket] = stats.get(bucket,0)+1
for k in sorted(stats): print(f'{k}: {stats[k]}')
"

# Baseline B: Missing Frontmatter (author, version)
python3 -c "
import yaml, glob
for field in ['name','description','author','version']:
    missing = sum(1 for f in glob.glob('**/SKILL.md',recursive=True)
        if '.archive/' not in f and not yaml.safe_load(open(f).read().split('---',2)[1]).get(field))
    print(f'Missing {field}: {missing}')
"

# Baseline C: P0/P1/P2 Candidates
python3 -c "
import yaml, glob, re
p0 = []; p1 = []; p2 = []
for f in glob.glob('**/SKILL.md', recursive=True):
    if '.archive/' in f: continue
    with open(f) as fh: content = fh.read()
    parts = content.split('---',2)
    fm = yaml.safe_load(parts[1]) if len(parts)>=2 else {}
    desc = str(fm.get('description','')) if isinstance(fm,dict) else ''
    lines = content.count(chr(10))
    if len(desc) < 30: p0.append(f)
    has_trig = bool(re.search(r'(use when|triggers on|trigger:)', content, re.I))
    if not has_trig and len(desc) < 80: p1.append(f)
    if lines > 500: p2.append(f)
print(f'P0 (desc<30): {len(p0)}')
print(f'P1 (no trigger + desc<80): {len(p1)}')
print(f'P2 (>500 Zeilen): {len(p2)}')
"

# Baseline D: Token Budget
total_bytes=$(find . -name SKILL.md -not -path '*/.archive/*' -exec cat {} + | wc -c)
echo "Total: $total_bytes bytes = $((total_bytes / 4)) tokens"
```

**Vorteil:** Alle 4 Baselines sind in <30s erhoben. Die Queen hat Ground Truth
bevor die Bienen landen.

---

## ⚠️ KRITISCH: Queen Baseline "Confidently Wrong" Pitfall

**Validated 2026-07-16:** Queen mass "12 Descriptions <30 chars" und war KOMPLETT
ÜBERZEUGT, das sei die richtige Zahl. Die 4 Bienen fanden ebenfalls "12 Skills
with short descriptions" — scheinbar 100% Match.

**Was wirklich passierte:** Die 12 Skills hatten nicht "kurze Descriptions",
sondern **leere oder fehlende Description-Strings**. Der YAML-Parser fiel
auf den `name`-Key zurück (`description: ~` oder fehlendes Feld).
Die Queen-Baseline hat `len(str(fm.get('description', '')))` gemessen und
korrekt <30 bekommen — aber **die Metrik war richtig, die Ursache falsch.**

### Wie es auffiel

| Aspekt | Queen Baseline | Bee A | Wahrheit |
|--------|:--------------:|:-----:|:---------:|
| Anzahl <30 desc | 12 | 12 | ✅ Korrekt |
| Root Cause | "kurze Texte" | "leere/falsche YAML-Parse" | ❌ Queen falsch |
| Beispiel | audio.md desc="17 Zeichen" | audio.md desc = `>` multiline-fallout | Bee richtig |

**Biene A hat die korrekte Root-Cause geliefert:**
```
- creative/audio/SKILL.md: description ist ein mehrzeiliger
  YAML-Block mit `>-` der zu `None`-Parse führt
```

### Warum das passiert

1. **Queen misst Quantität, nicht Qualität.** `len(description)` ist eine
   Zahl — sie sagt nichts über den Inhalt. 12× <30 ist die Metrik, aber
   die Ursache kann sein: leeres Feld, YAML-Parse-Fail, falsches Type-Coercion.
2. **Der Quick-Baseline-Scan liefert Metriken, keine Diagnose.**
   Die 40s-Scan-Sequenz ist optimiert für Geschwindigkeit, nicht für
   Root-Cause-Analyse.
3. **Confirmation Bias:** Wenn die Queen 12 misst und die Biene 12 findet,
   denkt sie "100% Match" und übersieht dass beide die gleiche Zahl aus
   unterschiedlichen Gründen haben.

### Lösung: Triple-Gate Cross-Check

```python
# Gate 1: Metrik-Vergleich (Queen vs Bee)
if queen_count == bee_count:
    # ⚠️ GLEICHE ZAHL ≠ GLEICHE ANTWORT
    # → Gate 2 auslösen
    pass

# Gate 2: Root-Cause-Validierung
# Queen: "ich habe 12. Biene: ich habe 12."
# → Stopp und prüfe: STIMMEN DIE 12 ÜBEREIN?
# Prüfe: Königin liest liste_der_bee vs queen_liste_vorher
queen_list = {'audio', 'audiobook', 'hermes-gateway', ...}  
bee_list   = {'audio', 'audiobook', '...'}  # hoffentlich gleich!
if queen_list == bee_list:
    # Nun prüfe ROOT CAUSE: "warum sind die kurz?"
    # Biene sagt "YAML-Parse-Problem" → Queen prüft live
    pass

# Gate 3: Stichprobe der Bienen-Methodik
# War Biene schneller als Queen? (Biene A hatte METRIKEN + ROOT CAUSE
# in einer Phase — Queen hatte nur METRIKEN aus Baseline)
# → Wenn Biene tiefer gräbt: VERTRAUE Biene für Root Cause
```

### Faustregel

> **Wenn Queen + Biene die gleiche Zahl finden, aber unterschiedliche
> Ursachen nennen: vertraue der Biene für die Ursache.**

Begründung: Die Biene hat mehr Zeit (2-4 Min vs 40s) und kann
Read-In-Depth machen (SKILL.md öffnen, YAML parsen, Fehler lesen).
Die Queen-Baseline ist ein Surface-Scan.

---

## Post-Fix Verification Loop (validated 2026-07-16)

Nachdem die Queen alle P0/P1 Fixes angewendet hat, DISPATCHET sie KEINE
neuen Bienen für den ersten Verify-Schritt. Stattdessen:

### Phase 1: Queen re-run same baseline (30s)

```bash
cd ~/.hermes/skills

# Re-run ALLE Baseline-Metriken
python3 -c "
import yaml, glob
# ... gleicher Code wie Queen Baseline ...
errors = 0
for f in glob.glob('**/SKILL.md', recursive=True):
    if '.archive/' in f: continue
    try:
        with open(f) as fh:
            parts = fh.read().split('---', 2)
        if len(parts) < 2: continue
        yaml.safe_load(parts[1])
    except: errors += 1
print(f'YAML errors: {errors}')
"

# Ergebnis 2026-07-16:
# YAML errors: 4 → 0 ✅
# Descriptions <30 chars: 12 → 0 ✅
# Descriptions >150 chars: 8 → 0 ✅
# Missing author: 4 → 0 ✅
# Missing version: 2 → 0 ✅
# Shebang without +x: 13 → 0 ✅
# Python Syntax Errors: 1 → 0 ✅
```

**Vorteil:** Identische Metrik = verlässlicher Vorher/Nachher-Vergleich.
Keine neuen Bienen nötig — die Queen validiert in 30s alle 43 Fixes.

### Phase 2: Verify-Bienen für unabhängige Validation (optional)

Erst NACH Queen-Self-Verify werden 2 Verify-Bienen dispatched:

| Biene | Scope | Was prüfen? |
|-------|-------|-------------|
| **V1 — Generic Verify** | Alle P0/P1 Fixes | 0 YAML-Errors, 0 <30 desc, 0 >150 desc, 0 missing fields, 0 broken shebangs, 0 syntax errors |
| **V2 — Content Verify** | Alle 12 neu geschriebenen Descriptions | Beginnt mit "Use when", 30-150 chars, endet mit Punkt, YAML gültig, keine Info verloren |

**Warum 2 und nicht 4 Bee-Welle?** Weil die Queen bereits 100% der Metrik-Fixes
selbst validiert hat. Die Verify-Bienen sind nur Insurance:
- V1 bestätigt: "ja, die Queen hat nichts übersehen"
- V2 prüft die CONTENT-QUALITÄT der neuen Descriptions, nicht nur die Metrik

### Verify-Bienen Briefing (Templates)

**V1 — Generic Verify:**
```
Du bist Verify-Biene V1 in Yunos Skill-Audit Welle 2.

Die Königin hat folgende Fixes angewendet:
(1) 4 YAML-Parse-Errors behoben
(2) 12 Descriptions <30 chars erweitert
(3) 1 Syntax-Error in robust-watcher.py behoben
(4) 13 Shebang-Scripts mit chmod +x versehen
(5) 5 fehlende author/version Frontmatter-Felder ergänzt
(6) 8 überlange Descriptions >150 chars gekürzt

DEINE TASKS (READ-ONLY):
1. Verifiziere: 0 YAML-Parse-Errors
2. Verifiziere: 0 Descriptions <30 chars
3. Verifiziere: 0 Descriptions >150 chars
4. Verifiziere: 0 Shebang-Scripts ohne +x
5. Verifiziere: 0 Skills ohne author oder version
6. Berichte: PASS/FAIL pro Check mit Details

OUTPUT-CONSTRAINTS (PFLICHT):
- 0 mid-sentence boldface, 0 em-dashes
- SELF-REPORT am Ende: "N tool-calls, PASS/FAIL pro Check"
- Sprache: Deutsch

MAX 8 tool-calls.
```

**V2 — Content Verify:**
```
Du bist Verify-Biene V2 in Yunos Skill-Audit Welle 2.

Die Königin hat 12 kritische Skill-Descriptions neu geschrieben
mit "Use when..." Trigger-Phrasen. Geänderte Skills: [Liste]

DEINE TASKS (READ-ONLY):
1. Lese jede der 12 SKILL.md-Dateien und prüfe:
   (a) Description beginnt mit "Use when" oder hat Trigger-Phrase
   (b) Description ist 30-150 chars lang
   (c) Description endet mit Punkt
   (d) YAML ist gültig (kein Parse-Error)
2. Berechne die NEUE Trigger-Coverage über alle 298 Skills
3. Liste die 12 Skills mit NEUEN Descriptions als Tabelle
4. Prüfe ob durch Kürzungen inhaltliche Infos verloren gingen

OUTPUT-CONSTRAINTS (PFLICHT):
- 0 mid-sentence boldface, 0 em-dashes
- SELF-REPORT am Ende: "N tool-calls, 12/12 PASS oder FAIL Details"
- Sprache: Deutsch

MAX 8 tool-calls.
```

---

## Trigger Coverage Metric — Wichtigster Metric-Caveat

**Validated 2026-07-16:** Trigger-Coverage war PRE-AUDIT **64%**.
Nach den Description-Fixes: **35%**. Was ist passiert?

**Root Cause:** Der Pre-Audit-Check (`grep -qiE ... 'use when' ...`) hat
auch Skills mit 100-Zeilen-Trigger-Listen im Body als "triggered" gezählt.
Der Skill `multi-agent-cluster-patterns` allein hat ~30 Trigger-Begriffe
— der check matcht auf die Hälfte aller Skills weil generische Trigger
wie "parallel worker coordination" in jeder Skill-Description vorkommen.

**Fix:** Trigger-Coverage MUSS getrennt gemessen werden:
1. **Frontmatter-Trigger** (description beginnt mit "Use when") — **harte Coverage**
2. **Body-Trigger** (trigger_keywords/triggers/YAML-Array) — **weiche Coverage**
3. **Nur Frontmatter-Trigger zählen für Quality-Metric** — Body-Trigger sind
   Artefakte von Skills mit riesigen Listen

**Empfehlung für zukünftige Audits:**
```python
# Harte Coverage: description.startswith('Use when')
# Weiche Coverage: trigger: im Body
hard = sum(1 for ... if desc.startswith('Use when'))
soft = sum(1 for ... if 'trigger:' in content)
print(f'Hard: {hard}/{total} ({hard*100//total}%)')
print(f'Soft: {soft}/{total} ({soft*100//total}%)')
```

---

## Complete Audit Flow (Phase 0 → End Report)

```
Phase 0: Quick-Scan (<10s)
  ├── find ~/.hermes/skills -name SKILL.md | wc -l
  ├── find ~/.hermes/skills -name '*.py' | wc -l
  └── du -sh ~/.hermes/skills

Phase 1: Dispatch 4 Scout-Bienen (parallel, 2-4 Min)
  ├── Bee A: Frontmatter/Description
  ├── Bee B: Trigger/Obsolescence
  ├── Bee C: Structure/Size
  ├── Bee D: Overlap/Duplicates
  └── QUEEN PARALLEL: Baseline Scans (<30s)
        ├── Description-Length-Distribution
        ├── Missing Frontmatter
        ├── P0/P1/P2 Candidates
        └── Token Budget

Phase 2: Queen-Verify Matrix (nach Bienen-Landung, <2 Min)
  ├── Metrik-Vergleich Queen vs Bee A/B/C/D
  ├── Triple-Gate: Zahlen gleich? → Root-Cause prüfen
  ├── Diskrepanzen dokumentieren (Gate 2/3)
  └── Priorisierte Fix-Liste (P0/P1/P2)

Phase 3: Fix Application (Queen direkt, 3-5 Min)
  ├── P0: YAML-Errors, <30 desc, Syntax-Errors
  ├── P1: Shebangs, Frontmatter, >150 desc
  └── [optional] P2: Monolithe, Broken Refs, Overlap

Phase 4: Post-Fix Verify (Queen baseline re-run, 30s)
  ├── Re-run ALLE Baseline-Metriken
  ├── Vorher/Nachher-Tabelle
  └── Wenn 0 Errors → dispatch 2 Verify-Bienen (optional)

Phase 5: Verify-Bienen (parallel, 60-90s)
  ├── V1: Generic Verify aller P0/P1 Fixes
  └── V2: Content Verify der neuen Descriptions

Phase 6: End Report (<5 Min)
  ├── Executive Summary
  ├── Methode + Bienen-Statistiken
  ├── Ergebnisse: P0/P1/P2 Vorher/Nachher
  ├── Statistik-Distribution (Post-Fix)
  └── P2 offene Items + Memory-Update
```

---

## Vergleiche: Vorher vs Nachher (2026-07-16)

| Metrik | Vorher | Nachher | Status |
|--------|:------:|:-------:|:------:|
| YAML Parse Errors | 4 | 0 | ✅ |
| Descriptions <30 chars | 12 | 0 | ✅ |
| Descriptions >150 chars | 8 | 0 | ✅ |
| Missing author | 4 | 0 | ✅ |
| Missing version | 2 | 0 | ✅ |
| Shebang without +x | 13 | 0 | ✅ |
| Python Syntax Errors | 1 | 0 | ✅ |
| Trigger Coverage (hard) | ~35% | ~35% | ⚠️ Same (descriptions changed, not structure) |
| Active Skills | 298 | 298 | ✅ |
| Total Token Budget | ~980K | ~980K | ✅ |

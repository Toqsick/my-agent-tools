# Queen Baseline Pre-Execute — Skill-Audit Worked Example

**Datum:** 2026-07-16
**Kontext:** Vollständiger Skill-Audit der Hermes-Bibliothek (298 Skills, ~980K Tokens)
**Pattern:** Queen dispatches 4 Scout-Bienen, führt parallel eigene Baseline-Scans durch

---

## Situation

- 298 aktive Skills in `~/.hermes/skills/`
- 193 archivierte Skills (`.archive/`)
- 85 Scripts, 0 Syntax-Errors
- 4 Bienen dispatched für Health-Audit (Quality, Content, Structure, Performance)

## Queen Parallel-Arbeit (Werkstatt-konform: reine READ-ONLY Messungen)

### 1. Description-Length-Distribution (8s)

```bash
cd ~/.hermes/skills
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
```

**Ergebnis 2026-07-16:**
```
<30 chars: 12 (P0!)
60-200 chars: 139
<60 chars: 152 (P1)
200-600 chars: 3
```

### 2. Missing Frontmatter (5s)

```bash
python3 -c "
import yaml, glob
for field in ['name','description','author','version']:
    missing = sum(1 for f in glob.glob('**/SKILL.md',recursive=True)
        if '.archive/' not in f and not yaml.safe_load(open(f).read().split('---',2)[1]).get(field))
    print(f'Missing {field}: {missing}')
"
```

**Ergebnis 2026-07-16:**
```
Missing name: 0
Missing description: 0
Missing author: 4
Missing version: 2
```

### 3. Broken-References-Deep-Dive (8s)

```bash
python3 -c "
import os, re, glob
broken = []
for f in glob.glob('**/SKILL.md', recursive=True):
    if '.archive/' in f: continue
    d = os.path.dirname(f)
    with open(f) as fh:
        refs = re.findall(r'(?:references|scripts|assets|templates)/[\w./-]+', fh.read())
    for r in set(refs):
        if not os.path.exists(os.path.join(d,r)) and not os.path.exists(r):
            if not re.search(r'(<|>|\{|\}|foo|bar|example|DATE)', r):
                broken.append((f,r))
print(f'Real broken refs: {len(broken)}')
by_cat = {}
for f,r in broken:
    cat = f.split('/')[0]
    by_cat.setdefault(cat,[]).append(r)
for c in sorted(by_cat, key=lambda c: len(by_cat[c]), reverse=True):
    print(f'  {c}: {len(by_cat[c])}')
"
```

**Wichtig:** Falsche Positive (Template-Platzhalter) rausfiltern:
- `references/phaseN-` = Template (enthält `N-`)
- `templates/template.html` = Template (Wort "template" im Pfad)
- `DATE` = Platzhalter
- `<foo>` oder `{bar}` = Platzhalter

**Ergebnis 2026-07-16:**
```
Real broken refs: 280
creative: 68 (Bundle-Skills ohne references/)
software-development: 46 (Bundle-Skills)
devops: 37
productivity: 29
orchestration: 14
voice-assistant-bots: 11
note-taking: 10
```

**Kategorisierung:** 132 broken refs weil das Verzeichnis nicht existiert (Bundle-Skills), 148 weil die Datei im existierenden Verzeichnis fehlt.

### 4. Library Token Footprint (3s)

```bash
cd ~/.hermes/skills

# Pro Kategorie
for cat in $(find . -name SKILL.md -not -path '*/.archive/*' | sed 's|^\./||;s|/SKILL.md||' | awk -F'/' '{print $1}' | sort -u); do
  bytes=$(find "./$cat" -name SKILL.md -exec cat {} + 2>/dev/null | wc -c)
  count=$(find "./$cat" -name SKILL.md | wc -l)
  tokens=$((bytes / 4))
  printf "%-30s %3d skills %7d tokens\n" "$cat" "$count" "$tokens"
done

# Gesamt
total_bytes=$(find . -name SKILL.md -not -path '*/.archive/*' -exec cat {} + | wc -c)
echo "Total: $total_bytes bytes = $((total_bytes / 4)) tokens"
```

**Ergebnis 2026-07-16:**
```
software-development:   37 skills    140723 tokens
creative:               38 skills    122723 tokens
devops:                 25 skills    126967 tokens
orchestration:          26 skills     98948 tokens
Total: ~980K Tokens
```

### 5. P0/P1/P2 Candidate Identification (10s)

```bash
python3 -c "
import yaml, glob, re
p0 = []  # description <30 chars
p1 = []  # no trigger AND description <80 chars
p2 = []  # >500 lines
for f in glob.glob('**/SKILL.md', recursive=True):
    if '.archive/' in f: continue
    with open(f) as fh:
        content = fh.read()
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
```

**Ergebnis 2026-07-16:**
```
P0 (desc<30): 12
P1 (no trigger + desc<80): 201
P2 (>500 Zeilen): 20
```

## Queen-Verify-Matrix

Template für Cross-Check bei Bienen-Landung:

```python
verify_matrix = """
## Queen Cross-Check Matrix

| Metrik | Queen Baseline | Bee A | Bee B | Bee C | Bee D | Status |
|--------|:-------------:|:-----:|:-----:|:-----:|:-----:|:------:|
| Active Skills | 298 | — | — | 298 | — | ✅ Match |
| Broken Refs | 280 | 0 | — | — | — | ❌ Bee falsch |
| P0 Candidates | 12 | — | 12 | — | — | ✅ Match |
| P1 Candidates | 201 | — | — | — | — | ⚠️ Bee nicht geprüft |
| P2 Monoliths | 20 | — | — | — | 18 | ⚠️ Abweichung |
"""
```

## Queen-Synthese

Nachdem Bienen gelandet und Cross-Check abgeschlossen → Synthese-Report:

```markdown
## Queen-Synthese

### Biene A (Quality): N findings
- P0: N kritische Descriptions (bestätigt durch Queen Baseline)
- P1: N no-trigger skills (QUEEN BASELINE: 201 — Abweichung Biene!)

### Biene B (Content): N findings
- Frontmatter: 6 missing fields (bestätigt durch Queen Baseline)

### Biene C (Structure): N findings
- Total Skills: 298 (bestätigt durch Queen Baseline)

### Biene D (Performance): N findings
- Token Budget: ~980K (bestätigt durch Queen Baseline)

### Priorisierte Fix-Strategie
P0 — Sofort (Queen direkt):
1. 12 Skills mit description <30 chars → neue Description + Trigger
2. 6 Skills mit missing Frontmatter → author/version setzen

P1 — Welle 2 (Bienen + Queen):
3. Top-50 weak descriptions mit Trigger-Coverage erhöhen
4. 280 broken references kategorisieren + patchen

P2 — Nächster Polish-Cycle:
5. 20 Monolithe >500 Zeilen → references/ auslagern
6. 201 weak descriptions systematisch umschreiben
```

## Lessons

1. **Queen kann 5 unabhängige Baseline-Metriken in <40s erheben.** Bienen benötigen 2-4 Min für ihren ersten Output.
2. **Der Cross-Check bei Bienen-Landung ist der kritischste Moment.** Die Queen sieht sofort welche Bienen halluziniert haben (Self-Report ≠ Queen-Baseline).
3. **P0/P1/P2 Kategorisierung ist essentiell.** Ohne Priorisierung werden 280 broken refs und 201 weak descriptions unübersichtlich. Mit Kategorisierung: Queen fixt P0 direkt, Bienen kümmern sich um P1, P2 wird notiert.
4. **Falsche Positive bei Broken Refs sind der häufigste Audit-Fehler.** Template-Platzhalter (DATE, `<foo>`, `{bar}`) werden vom Regex erfasst, sind aber keine echten broken refs. Immer mit `re.search` rausfiltern, sonst sind 10% der "broken refs" false positives.
5. **Werkstatt-Regel bleibt erhalten:** Queen macht in Phase 1 keine Edits, keine Memory-Mutationen. Baseline ist reine Inspektion. P0-Fixes kommen erst nach Bienen-Landung + Cross-Check.

---

## Quick-Start (für schnelle Audits)

```bash
# Einzeiler: Alle 5 Baselines in <30s
cd ~/.hermes/skills
python3 -c "
import yaml, glob, os, re
p0=[]; p1=[]; p2=[]; broken=[]; stats={}; front={f:0 for f in ['author','version']}
for f in glob.glob('**/SKILL.md', recursive=True):
    if '.archive/' in f: continue
    c=open(f).read(); p=c.split('---',2); d=os.path.dirname(f)
    fm=yaml.safe_load(p[1]) if len(p)>=2 else {}
    if isinstance(fm,dict):
        dl=len(str(fm.get('description',''))); l=c.count(chr(10))
        if dl<30: p0.append(f)
        if not re.search(r'(use when|triggers on|trigger:)',c,re.I) and dl<80: p1.append(f)
        if l>500: p2.append(f)
        for k in front:
            if not fm.get(k): front[k]+=1
        b='<30' if dl<30 else '<60' if dl<60 else '60-200' if dl<=200 else '200-600' if dl<=600 else '>600'
        stats[b]=stats.get(b,0)+1
    for r in set(re.findall(r'(?:references|scripts|assets|templates)/[\w./-]+', c)):
        fp=os.path.join(d,r)
        if not os.path.exists(fp) and not os.path.exists(r) and not re.search(r'(<|>|\{|\}|foo|bar|DATE)', r):
            broken.append((f,r))
print(f'Beschreibung: {len(p0)} P0, {len(p1)} P1 | BrokenRefs: {len(broken)} | Monolithe: {len(p2)} | Frontmatter: {front}')
for k in sorted(stats): print(f'  {k}: {stats[k]}')
"
```

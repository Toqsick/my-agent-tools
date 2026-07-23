# Trigger-Coverage KPI — Skill Catalog Quality Metric

> **Stand:** 2026-07-16  
> **Gemessen von:** Yuno (Queen Baseline + Biene P1)  
> **Scope:** 299 aktive Skills in `~/.hermes/skills/`

---

## Definition

**Trigger-Coverage** = Anteil der Skills deren Description mit `Use when` beginnt.
Eine hohe Coverage (40%+) bedeutet: AI-Agenten können den richtigen Skill per Trigger-Phrase finden.

## Messmethodik

```python
import yaml, glob, os

home = os.path.expanduser('~')
total = use_when = no_trigger = 0
buckets = {'<30': 0, '30-60': 0, '60-100': 0, '100-150': 0, '>150': 0}

for f in glob.glob(f'{home}/.hermes/skills/**/SKILL.md', recursive=True):
    if '.archive/' in f or '.curator_backups/' in f: continue
    total += 1
    try:
        with open(f) as fh:
            parts = fh.read().split('---', 2)
        if len(parts) < 2: continue
        fm = yaml.safe_load(parts[1])
        if not isinstance(fm, dict): continue
        desc = str(fm.get('description', ''))
        dlen = len(desc)
        if dlen < 30: buckets['<30'] += 1
        elif dlen < 60: buckets['30-60'] += 1
        elif dlen < 100: buckets['60-100'] += 1
        elif dlen < 150: buckets['100-150'] += 1
        else: buckets['>150'] += 1
        if desc.startswith('Use when'): use_when += 1
        elif not any(t in desc.lower() for t in ['use when', 'trigger', 'invoke']):
            no_trigger += 1
    except: pass

print(f'Total:\t{total}')
print(f'Use when:\t{use_when} ({use_when*100//total}%)')
print(f'No trigger:\t{no_trigger} ({no_trigger*100//total}%)')
for k in ['<30','30-60','60-100','100-150','>150']:
    print(f'{k}:\t{buckets[k]}')
```

## Current State (2026-07-16 post-Polish)

| Metrik | Wert | Ziel |
|---|---|---|
| Total Skills | 299 | — |
| Use when Trigger | 83 (27%) | **40%+** |
| Kein Trigger-Phrase | 213 (71%) | <50% |
| Description <30 chars | 0 | 0 ✅ |
| Description 30-60 chars | ~160 | <50 (nächste Polish-Welle) |

## Kategorien der 213 Skills ohne Trigger

Bei der 2026-07-16 Analyse zeigte sich:

| Kategorie | Ungefährer Anteil | Beispiele |
|---|---|---|
| Kurze Standard-Beschreibung (<60 chars) | ~70% | `description: Tools for X.` |
| Längere Beschreibung aber ohne Trigger | ~20% | `description: Runs X, Y, Z processes...` |
| Spezialfall: YAML Multiline ohne Trigger | ~10% | `description: \| ...` |

## Pipeline für Coverage-Verbesserung

1. **Nächste Polish-Runde (Runde 3):** ~160 Skills mit 30-60 char descriptions ohne Trigger
2. **Queen Pre-Execute:** Königin macht 50 Rewrites selbst
3. **Verify-Biene:** Cross-Check der Rewrites gegen Filesystem
4. **Cron-Watchdog (optional):** Monatlicher Coverage-Scan mit Alarm bei <38%

## Warum 40%+ Ziel?

- Skills mit `Use when` im Index werden von Hermes auto-detected (available_skills injection)
- Je höher die Coverage, desto weniger manuelle `skill_view()` Calls des Agents
- 27% nach 2 Polish-Runden bedeutet: **~37 weitere Rewrites nötig** für die nächste 10%-Stufe

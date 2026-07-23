---


name: quality-gate-runner
description: 'Use when user asks to run Markdown quality gates, validate a Daily Note, check humanization output, or diagnose parser-blocked gate commands. NOT for general prose editing or source-code linting. Runs deterministic EmDash, Boldface, InlineHeader, NegParallel, and WikiLinks checks via the safe execute_code path.'
version: 1.1.0
author: Yuno
agent: Yuno
lane: koenigin
trigger_keywords:
- quality gate
- self test
- em dashes
- boldface
- wikilinks
- humanisieren
- gate check
- daily prüfen
license: MIT
keywords: ['code', 'user', 'asks', 'markdown', 'quality']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['critic-gate', 'obsidian', 'output-validator']
---



# Quality Gate Runner

> Führt die 5 Quality-Gates aus `daily-briefing §2.8` auf einer Markdown-Datei aus.
> Nutzt `execute_code` statt bash weil der Terminal-Parser `bash -c` mit grep/sed blockt.
> Entstanden aus der 2026-07-18→19 Daily-Rekonstruktion.

## Wann anwenden

- Nach dem Schreiben oder Humanisieren einer Daily-Note (oder jedem Markdown-Dokument)
- Bevor der Self-Report ausgegeben wird
- Nach jeder Humanisierungs-Iteration
- Immer wenn der bash-Quality-Gate aus §2.8 den Parser-Blocker triggert

## Ausführung

```python
import re

f = "/pfad/zur/datei.md"
with open(f, "r", encoding="utf-8") as fh:
    content = fh.read()

em = content.count('—')
boldface = len(re.findall(r'\*\*[^*]*\*\*', content))
inline_hdr = len(re.findall(r'^\s*-\s+\*\*[^*]+\*\*', content, flags=re.MULTILINE))
neg_parallel = len(re.findall(r'kein \w+ (nötig|erforderlich)', content))
wiki_links = re.findall(r'\[\[([^\]]+)\]\]', content)
size = len(content)

results = [
    ("EmDashes", "≤1", em),
    ("Boldface", "0", boldface),
    ("InlineHdr", "0", inline_hdr),
    ("NegParall", "0", neg_parallel),
    ("WikiLinks", "≥3", len(wiki_links)),
]

print(f"## Quality Gate — {f.split('/')[-1]}")
print()
print("| Gate | Ziel | Wert | Status |")
print("|---|---|---|---|")
for name, target, val in results:
    ok = (
        (name == "EmDashes" and val <= 1) or
        (name == "Boldface" and val == 0) or
        (name == "InlineHdr" and val == 0) or
        (name == "NegParall" and val == 0) or
        (name == "WikiLinks" and val >= 3)
    )
    status = "PASS ✅" if ok else "FAIL ❌"
    print(f"| {name} | {target} | {val} | {status} |")

print(f"\n**Datei:** {f}")
print(f"**Größe:** {size} Bytes")
all_pass = all(
    (r[0] == "EmDashes" and r[2] <= 1) or
    (r[0] == "Boldface" and r[2] == 0) or
    (r[0] == "InlineHdr" and r[2] == 0) or
    (r[0] == "NegParall" and r[2] == 0) or
    (r[0] == "WikiLinks" and r[2] >= 3)
    for r in results
)
print(f"**Gesamt:** {'✅ ALLE PASS' if all_pass else '❌ Mindestens ein FAIL — humanisieren und erneut prüfen'}")
```

## Humanisierungs-Checkliste (wenn FAIL)

| Gate | Typischer Fix |
|------|--------------|
| EmDashes FAIL | `content.replace(' — ', ' - ').replace('—', '-')` — alle durch normale Bindestriche ersetzen |
| Boldface FAIL | Mid-Sentence `**xyz**` → `xyz` (ohne Bold). Nur H1/H2-Header als `##` belassen. |
| InlineHdr FAIL | `-**` am Listenanfang → echten `###`-Header daraus machen oder auf normales List-Item wechseln |
| NegParall FAIL | `kein X nötig` → umformulieren zu aktivem Satz ohne Negation |
| WikiLinks FAIL | Plain-Text-Referenzen in `[[echte WikiLinks]]` umwandeln — mindestens 3 |

## Iterations-Erwartung

Passe davon aus, dass der erste Draft **2-3 FAILs** hat. Erwarte 2-3 Durchläufe.

Typisches Muster:
- Pass 1: 2-4 FAIL (meist EmDashes + Boldface)
- Pass 2: 1 FAIL (Boldface hält sich am längsten)
- Pass 3: 0 FAIL → Self-Report ausgeben

## Cross-Reference

- `daily-briefing §2.8` — Die Spezifikation der 5 Gates
- `daily-briefing §0.5.7` — Humanisierungs-Loop mit 2-3 Pass-Erwartung
- `self-improving/references/quality-gate-parser-blocker-workaround.md` — Detaillierte Erklärung warum bash blockt
- `wiki-corpus-lint-runner` — Korpus-Skalierung derselben Gates auf 50+ MD-Files mit Auto-Fix + Cross-Link-Validation + Stand-Datum-Check

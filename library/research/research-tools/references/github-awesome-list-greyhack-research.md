# GitHub Awesome-list Research for GreyHack

Reference workflow from the 2026-06-19 Awesome-Hacking research pass.

## Source snapshot

- Source: `https://github.com/Toqsick/Awesome-Hacking`
- Local read-only snapshot: `/tmp/Awesome-Hacking`
- Commit: `f995379fe1fb87f8f3a981a77c6c601a2a21d50b`
- Last commit: `f995379 redesign the repository banner with a cleaner GitHub-style visual identity (#211)`
- README rows extracted: `81`
- Top-20 entries: `20`
- Later-research entries: `61`

## Output files created in this pattern

- `docs/security-research/README.md`
- `docs/security-research/awesome-hacking-source-snapshot.md`
- `docs/security-research/awesome-hacking-top20.md`
- `docs/security-research/awesome-hacking-catalog.csv`
- `docs/security-research/awesome-hacking-knowledge-base.csv`
- `docs/security-research/awesome-hacking-later-research.md`
- `docs/security-research/greyhack-relevance-schema.md`
- `docs/security-research/safety-review.md`

## Top-20 order used

1. CTF
2. Pentest Wiki
3. Shell
4. PayloadsAllTheThings
5. SecLists
6. Static Analysis
7. Fuzzing
8. Reversing
9. Cryptography
10. OSINT
11. Cyber Skills
12. Cyber Security University
13. Bug Bounty
14. Web Hacking
15. API Security Checklist
16. Node.js Security
17. Red Teaming Toolkit
18. Detection Engineering
19. Incident Response
20. Honeypots

## GreyHack safety boundary

Awesome-lists often contain real exploit tools, PoCs, credential material, and network targets. For GreyHack, transfer only:

- CTF/puzzle methodology
- Recon/enumeration structure
- Parser/testcase thinking
- Tool-design concepts
- Harmless dummy data
- Defensive/logging/documentation ideas

Do not port real exploit instructions, PoCs, credential lists, or external network targeting into GreyScript.

## Validation pattern

```bash
python3 - <<'PY'
import csv
from pathlib import Path
base=Path('docs/security-research')
files=[
  'README.md',
  'awesome-hacking-top20.md',
  'awesome-hacking-knowledge-base.csv',
  'awesome-hacking-catalog.csv',
  'awesome-hacking-later-research.md',
  'greyhack-relevance-schema.md',
  'safety-review.md',
  'awesome-hacking-source-snapshot.md',
]
for f in files:
    p=base/f
    assert p.is_file() and p.stat().st_size>0, f'{p} missing or empty'
cat=list(csv.DictReader((base/'awesome-hacking-catalog.csv').open(encoding='utf-8')))
kb=list(csv.DictReader((base/'awesome-hacking-knowledge-base.csv').open(encoding='utf-8')))
assert len(cat)==81
assert len(kb)==61
assert sum(1 for r in cat if r['top20']=='yes')==20
assert sum(1 for r in cat if r['top20']=='no')==61
print('docs validation ok:', len(cat), 'catalog rows,', len(kb), 'knowledge-base rows')
PY

git status --short -- docs src tools
```

Expected result: only documentation/plan paths changed; no `src/` or `tools/` GreyScript files changed.

## Pitfalls

- Do not assume the README table has leading pipes. This Awesome-Hacking README uses plain Markdown table rows like `[CTF](url) | Description`; parse on ` | ` rather than requiring `line.startswith('|')`.
- Do not trust old counts blindly. The prior plan assumed ~89 resources, but the actual snapshot contained 81.
- Keep the research pass read-only. If the user asked for Top-20 before scripts, do not edit `src/` or `tools/` until the Top-20 and safety review are approved.

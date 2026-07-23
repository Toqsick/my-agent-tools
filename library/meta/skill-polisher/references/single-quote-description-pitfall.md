# YAML Single-Quote Description Pitfall (2026-07-16)

## Problem

Beim String-Patching von SKILL.md-Descriptions schlaegt der Match fehl,
obwohl der Text optisch identisch aussieht:

```python
# Das hier funktioniert NICHT bei single-quoted YAML:
content = path.read_text()
old = 'description: Kurzer Text.'
if old in content:  # False! Raw-Text ist 'description: '\''Kurzer Text.'\'''
    content = content.replace(old, 'description: Neuer Text.', 1)
```

## Root Cause

YAML Frontmatter kann Descriptions als Single-Quoted Strings speichern:

```yaml
description: 'Kurzer Text.'
```

Der Raw-Text enthaelt dann die einfachen Anfuehrungszeichen:
`description: 'Kurzer Text.'` (RAW: description: 'Kurzer Text.')

Bei YAML-Parse (yaml.safe_load) werden die Quotes korrekt entfernt.
Aber bei **String-Patching auf Raw-Text** sind sie da.

## Erkennung

```bash
# RAW-Format der Description-Zeile anzeigen
grep '^description:' path/to/skill/SKILL.md
# Output: description: 'Kurzer Text.'  ← Quotes sind Teil des Textes!
```

## Fix: Triple-Varianten-Match

```python
old_desc = 'Kurzer Text.'
new_desc = 'Use when doing something important.'

# Pruefe ALLE YAML-Quote-Varianten:
for variant in [
    f'description: {old_desc}',                  # ohne Quotes
    f"description: '{old_desc}'",                 # single-quoted
    f'description: "{old_desc}"',                 # double-quoted
]:
    if variant in content:
        content = content.replace(variant, f'description: {new_desc}', 1)
        break
else:
    print(f'⚠️  Keine Variante gematcht: {file}')
```

## Verify

Nach jedem Patch:

```bash
python3 -c "import yaml; yaml.safe_load(open('SKILL.md').read().split('---',2)[1])"
```

Wenn das ohne Exception durchlaeuft: YAML ist korrekt.

## Live-Demo (2026-07-16)

50 Description-Rewrites wurden durchgefuehrt:

| Status | Anzahl | Details |
|--------|-------:|---------|
| Auto-Match (unguoted) | 43 | Direkter String-Vergleich |
| Manual-Fix (single-quoted) | 7 | Mussten mit Quotes gematcht werden |
| **Total** | **50** | **0 YAML-Parse-Errors** |

Die 7 betroffenen Skills waren:
- `devops/webhook-subscriptions`
- `software-development/debugging-hermes-tui-commands`
- `software-development/plan`
- `software-development/python-debugpy`
- `software-development/requesting-code-review`
- `software-development/test-driven-development`
- `software-development/writing-plans`

```bash
# Finde alle Skills mit single-quoted descriptions (damit du sie vorher kennst):
find ~/.hermes/skills -name SKILL.md -not -path '*/.archive/*' \
  | xargs grep -l "^description: '" 2>/dev/null
```

---


name: context-mode
description: "Use when user asks for context mode, context window optimization, token sparsity. NOT for writing prose, creative content. Optimizes context window usage for AI coding agents via token-sparse techniques."
metadata:
  author: mksglu
  version: '1.0'
lane: worker-flash
reasoning_effort: high
author: Hermes Agent
version: 1.0.0
license: MIT
trigger_keywords: ['context', 'window', 'context-mode', 'mode', 'optimization']
keywords: ['context', 'window', 'token', 'user', 'asks']
last_curated: '2026-07-23'
curated_by: 'Yuno'
related_skills: ['hermes-context-budget', 'desktop-window-reconnaissance', 'session-handoff']
---

# Context Mode: Token-Sparsamkeit

Context-Mode ist eine Virtualisierungsschicht für Tool-Outputs. Große Ausgaben werden sandboxed, bevor sie in den Context fließen — reduziert Token-Verbrauch um bis zu 98%.

## Wann zu nutzen

Bei ALLEN Operationen die >20 Zeilen Output produzieren können:
- Log-Analyse, Build-Output, Test-Results
- API-Responses, JSON-Daten
- Browser-Snapshots, DOM-Struktur
- Git-Log, Diffs, Codebase-Statistiken
- Dependency-Trees, CI/CD-Output

## Prinzip

**Bash-Whitelist** (direkt ausführen, garantiert kleiner Output):
- `cd`, `ls`, `pwd`, `echo`, `cat` (kurze Dateien)
- `which`, `type`, `head`, `tail`, `wc`
- `export`, `unset`

**Alles andere** → Output vor dem Einlesen prüfen:
```bash

set -euo pipefail
# Schlecht: 5000 Zeilen Log direkt lesen
cat /var/log/syslog

# Gut: Erst Länge checken, dann einschränken
wc -l /var/log/syslog
tail -50 /var/log/syslog
grep "ERROR" /var/log/syslog | tail -20
```

## Regeln

1. **Immer `wc -l` oder `head` vor `cat`** bei unbekannten Dateien
2. **`grep` + `tail` statt vollständiges Lesen** bei Logs
3. **`jq` für JSON** statt rohes `cat`
4. **`--limit` Parameter** bei Hermes-Tools nutzen (`read_file` hat `limit=500`)
5. **Subagent-Briefings**: Explizit "Output >100 Zeilen → head/wc-l verwenden"

## Integration mit Hermes

Hermes hat bereits eingebaute Schutzmaßnahmen:
- `read_file` limitiert auf 500 Zeilen default
- `web_extract` summarisiert große Seiten
- Context-Compaction bei vollem Window

Der Context-Mode-Ansatz ergänzt dies durch bewusstes Output-Management BEIM Tool-Aufruf, nicht erst beim Lesen.

**Hinweis Modell-Ebene:** Context-Mode zähmt *Tool-Output*. Der andere große Kontext-Fresser ist auf **MiniMax-M3** (Session-Default) der erhaltene *Reasoning-Trace* (bis 49152 Token/Runde @ ultra, H-10-persistent) — den fängt Context-Mode nicht. Dafür `hermes-context-budget` → „M3-Thinking-Traces vs GLM-5.2". GLM-5.2 hat dieses Problem nicht.

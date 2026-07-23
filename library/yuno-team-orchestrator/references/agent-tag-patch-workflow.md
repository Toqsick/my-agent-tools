# Agent-Tag-Patch-Workflow

> **Stand:** 2026-07-15
> **Purpose:** Wie neue oder bestehende Skills mit `agent:` + `routing_hint:` getaggt werden, damit sie in der 52-Skill-Routing-Matrix (siehe `routing-table.md`) auftauchen und Yuno sie korrekt routen kann.

## Wann patchen?

Jeder Skill, den Yuno systematisch einer Persona zuordnen können soll, braucht zwei YAML-Frontmatter-Felder:

```yaml
---
name: skill-name
description: "..."
metadata:
  hermes:
    tags: [...]
    agent: "Engineer"          # <- PFLICHT wenn Routing gewünscht
    routing_hint: "..."        # <- PFLICHT: kurze Beschreibung wann dieser Skill läuft
---
```

## Erlaubte Agent-Werte

| Wert       | Wann nutzen                                    |
|------------|------------------------------------------------|
| `Yuno`     | Cross-domain Meta-Skills (Memory, Skill-Creation) |
| `Engineer` | Code, Refactoring, Debug, GitHub-Workflow     |
| `Researcher` | Web-Search, ArXiv, Fact-Check, Research-Tools |
| `Designer` | UI/UX, Visual Content, Images, Landing-Pages  |
| `Analyst`  | Data, Spreadsheets, Modeling, Calculations     |
| `Writer`   | Long-Form Content, Proposals, Copy             |
| `Verifier` | Audits, Bug-Hunt, Validation                   |

Falls unklar: `Yuno` (root).

## routing_hint-Schema

Kurz (max 80 Zeichen), aktions-fokussiert, mit Trigger-Wörtern:

```yaml
# GUT:
routing_hint: "Implementation Engineer for hard problems — build, refactor, debug"

# BESSER (mit Kontext):
routing_hint: "Plan mode — write actionable markdown plans to .hermes/plans/"

# SCHLECHT (zu generisch):
routing_hint: "useful skill"
```

## Patch-Workflow (3 Schritte)

### 1. Audit-Phase
Welche Skills haben schon `agent:`-Tags? Welche fehlen?

```bash
grep -L "agent:" ~/.hermes/skills/*/SKILL.md ~/.hermes/skills/*/*/SKILL.md 2>/dev/null
```

Liste alle ohne Tag → daraus ergibt sich der Patch-Backlog.

### 2. Patch-Phase
Pro Skill:
1. `read_file` auf SKILL.md
2. `patch` mit `old_string: 'metadata:\n  hermes:\n    tags:'` und `new_string` mit zusätzlichem `agent:` + `routing_hint:`
3. Konsistenz-Check: passt der Agent zur tatsächlichen Skill-Funktion?

### 3. Verification-Phase
Re-Run der Routing-Matrix in `routing-table.md`. Sollte jetzt einen Eintrag mehr haben.

```bash
cd /home/bratan/.hermes/skills/yuno-team-orchestrator
./scripts/personas.py list  # zeigt verfügbare Personas
```

Dann manuell in `routing-table.md` die Skill-Liste pro Persona erweitern.

## Pitfalls

- **Tags-Verwechslung**: `metadata.hermes.tags` ≠ `agent`. Erstere ist für Skill-Kategorisierung (z.B. `[design, ui]`), Letzteres ist Persona-Routing.
- **routing_hint zu lang**: max 80-100 Zeichen. Sonst wird die Routing-Matrix unleserlich.
- **Falscher Agent**: Code-Skill mit `agent: "Designer"` getaggt → falsche Routing. Im Zweifel nochmal in `personas.yaml` nachschauen was die Persona tatsächlich macht.
- **Vergessen zu testen**: Nach Patch: `route "trigger phrase"` aufrufen und schauen ob neuer Skill korrekt zugeordnet wird.

## Beispiel-Patch

**Vorher:**
```yaml
---
name: claude-coder
description: "Implementation engineer"
---
```

**Nachher:**
```yaml
---
name: claude-coder
description: "Implementation engineer"
metadata:
  hermes:
    tags: [code, engineering]
    agent: "Engineer"
    routing_hint: "Implementation Engineer for hard problems — build, refactor, debug code in any language"
---
```

## Siehe auch

- `routing-table.md` — die 52-Skill-Matrix mit allen getaggten Skills
- `personas.yaml` — die verbatim Persona-System-Prompts (single source of truth)
- `skill-curator-audit-2026-07-11.md` — letzter Audit-Bericht welche Skills fehlten